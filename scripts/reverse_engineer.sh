#!/bin/bash
#
# reverse_engineer.sh - Master Reverse Engineering Pipeline
# ==========================================================
# Extracts all data from classic Macintosh AOL tool binaries:
#   1. StuffIt archive extraction (unar)
#   2. Resource fork parsing (Python + macOS resource forks)
#   3. Art extraction: icons (ICN#, icl4, icl8, ics#) -> PNG, PICT -> PNG via sips
#   4. Sound extraction: snd resources -> WAV (stdSH and extSH; cmpSH/MACE skipped)
#   5. Text extraction: TEXT, STR, STR# resources -> plain text
#   6. FDO88 decompilation: DB* resources -> human-readable FDO88 source via atomforge-fdo-java
#   7. Web manifest generation: base64-encoded assets for the website
#
# Requirements:
#   - macOS (for resource fork access and sips)
#   - unar (brew install unar)
#   - Python 3.9+ with Pillow (pip install Pillow) and macresources (pip install macresources)
#   - Java 21+ (for atomforge-fdo-java)
#   - atomforge-fdo-java JAR built at $ATOMFORGE_JAR
#
# Usage:
#   ./reverse_engineer.sh [options]
#
# Options:
#   --sit-dir DIR      Directory containing .sit archives (default: ../binary sources/tools/)
#   --output DIR       Output directory (default: ../site_data/)
#   --atomforge JAR    Path to atomforge-fdo JAR
#   --skip-extract     Skip StuffIt extraction (use existing extracted_tools/)
#   --skip-resources   Skip resource extraction (use existing site_data/)
#   --skip-decompile   Skip FDO88 decompilation
#   --only-decompile   Only run FDO88 decompilation step
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Defaults
SIT_DIR="$PROJECT_DIR/binary sources/tools"
EXTRACTED_DIR="$PROJECT_DIR/extracted_tools"
OUTPUT_DIR="$PROJECT_DIR/site_data"
ATOMFORGE_JAR="${ATOMFORGE_JAR:-/Users/chrisk/Documents/source/atomforge-fdo-java/target/atomforge-fdo-2.0.0-SNAPSHOT.jar}"
SKIP_EXTRACT=false
SKIP_RESOURCES=false
SKIP_DECOMPILE=false
ONLY_DECOMPILE=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --sit-dir) SIT_DIR="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --atomforge) ATOMFORGE_JAR="$2"; shift 2 ;;
        --skip-extract) SKIP_EXTRACT=true; shift ;;
        --skip-resources) SKIP_RESOURCES=true; shift ;;
        --skip-decompile) SKIP_DECOMPILE=true; shift ;;
        --only-decompile) ONLY_DECOMPILE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=================================================="
echo "  AOL Tool Reverse Engineering Pipeline"
echo "=================================================="
echo "  SIT archives:  $SIT_DIR"
echo "  Extracted to:  $EXTRACTED_DIR"
echo "  Output:        $OUTPUT_DIR"
echo "  Atomforge JAR: $ATOMFORGE_JAR"
echo "=================================================="

# ---- STEP 1: Extract StuffIt Archives ----
if [ "$SKIP_EXTRACT" = false ] && [ "$ONLY_DECOMPILE" = false ]; then
    echo ""
    echo "[Step 1] Extracting StuffIt archives..."
    mkdir -p "$EXTRACTED_DIR"
    count=0
    for sit in "$SIT_DIR"/*.sit; do
        [ -f "$sit" ] || continue
        name="$(basename "${sit%.sit}")"
        echo "  Extracting: $name"
        unar -o "$EXTRACTED_DIR/$name" -f "$sit" 2>/dev/null || echo "    WARNING: unar failed for $name"
        count=$((count + 1))
    done
    echo "  Extracted $count archives"
else
    echo "[Step 1] Skipping StuffIt extraction"
fi

# ---- STEP 2: Extract Resources (art, sounds, text, FDO88 binaries) ----
if [ "$SKIP_RESOURCES" = false ] && [ "$ONLY_DECOMPILE" = false ]; then
    echo ""
    echo "[Step 2] Extracting resources from all tools..."
    python3 "$SCRIPT_DIR/extract_resources.py" "$EXTRACTED_DIR" "$OUTPUT_DIR"
else
    echo "[Step 2] Skipping resource extraction"
fi

# ---- STEP 3: Decompile FDO88 Forms ----
if [ "$SKIP_DECOMPILE" = false ]; then
    echo ""
    echo "[Step 3] Decompiling FDO88 forms with atomforge-fdo-java..."

    if [ ! -f "$ATOMFORGE_JAR" ]; then
        echo "  ERROR: atomforge JAR not found at $ATOMFORGE_JAR"
        echo "  Build it with: cd /path/to/atomforge-fdo-java && mvn package -DskipTests"
        exit 1
    fi

    # Compile the batch decompiler if needed
    if [ ! -f "$SCRIPT_DIR/Fdo88BatchDecompile.class" ]; then
        echo "  Compiling batch decompiler..."
        javac -cp "$ATOMFORGE_JAR" "$SCRIPT_DIR/Fdo88BatchDecompile.java"
    fi

    # Run decompilation
    cd "$SCRIPT_DIR"
    java -cp "$ATOMFORGE_JAR:." Fdo88BatchDecompile \
        "$OUTPUT_DIR/fdo88" \
        "$OUTPUT_DIR/fdo88_decompiled"
    cd "$PROJECT_DIR"
else
    echo "[Step 3] Skipping FDO88 decompilation"
fi

# ---- STEP 4: Generate Web Data Files ----
if [ "$ONLY_DECOMPILE" = false ]; then
    echo ""
    echo "[Step 4] Generating web data files..."

    # Generate tool manifest with base64-encoded assets
    python3 << 'PYEOF'
import json, base64, os

manifest_path = os.environ.get('OUTPUT_DIR', 'site_data') + '/manifest.json'
site_data_dir = os.environ.get('OUTPUT_DIR', 'site_data')
project_dir = os.environ.get('PROJECT_DIR', '.')

if not os.path.exists(manifest_path):
    print("  No manifest.json found, skipping web data generation")
    exit(0)

with open(manifest_path) as f:
    manifest = json.load(f)

web_data = {'tools': {}, 'stats': manifest.get('stats', {})}
if not web_data['stats']:
    web_data['stats'] = {
        'total_tools': manifest.get('total_tools', 0),
        'total_art': manifest.get('total_art', 0),
        'total_sounds': manifest.get('total_sounds', 0),
        'total_text': manifest.get('total_text', 0),
        'total_fdo88': manifest.get('total_fdo88_forms', 0)
    }

for tool_name, tool in manifest['tools'].items():
    entry = {
        'name': tool_name,
        'versions': tool.get('versions', []),
        'resource_summary': tool.get('resource_summary', {}),
        'has_aotk': tool.get('has_aotk', False),
        'art_count': tool.get('art_count', 0),
        'sound_count': tool.get('sound_count', 0),
        'text_count': tool.get('text_count', 0),
        'fdo88_count': tool.get('fdo88_count', 0),
        'text': tool.get('text', []),
        'icons': [], 'picts': [], 'sounds': []
    }

    seen = set()
    for art in tool.get('art', []):
        path = os.path.join(site_data_dir, art['path'])
        at = art['type']
        if at in ('icl8','icl4','ICN#','ics8','ics4','ics#','ICON','CURS'):
            key = f"{at}_{art['id']}"
            if key in seen: continue
            seen.add(key)
            if os.path.exists(path) and path.endswith('.png'):
                try:
                    with open(path,'rb') as f: b64=base64.b64encode(f.read()).decode()
                    entry['icons'].append({'type':at,'id':art['id'],'name':art.get('name'),'data':b64})
                except: pass
        elif at == 'PICT':
            if os.path.exists(path) and path.endswith('.png') and os.path.getsize(path) < 100000:
                try:
                    with open(path,'rb') as f: b64=base64.b64encode(f.read()).decode()
                    entry['picts'].append({'id':art['id'],'name':art.get('name'),'data':b64})
                except: pass

    for snd in tool.get('sounds', []):
        path = os.path.join(site_data_dir, snd['path'])
        if os.path.exists(path) and path.endswith('.wav') and 100 < os.path.getsize(path) < 500000:
            try:
                with open(path,'rb') as f: b64=base64.b64encode(f.read()).decode()
                entry['sounds'].append({'id':snd['id'],'name':snd.get('name'),'data':b64})
            except: pass

    web_data['tools'][tool_name] = entry

out = os.path.join(project_dir, 'tool_manifest.js')
with open(out, 'w') as f:
    f.write('window.__TOOL_MANIFEST = ')
    json.dump(web_data, f)
    f.write(';\n')
print(f"  tool_manifest.js: {os.path.getsize(out)/1024/1024:.1f} MB")
PYEOF

    # Generate FDO88 forms JS from decompiled manifest
    FDO_MANIFEST="$OUTPUT_DIR/fdo88_decompiled/fdo88_manifest.json"
    if [ -f "$FDO_MANIFEST" ]; then
        python3 -c "
import json, os
with open('$FDO_MANIFEST') as f:
    m = json.load(f)
by_tool = {}
for form in m['forms']:
    t = form['tool']
    if t not in by_tool: by_tool[t] = []
    by_tool[t].append({'db':form['db'],'record':form['record'],'source':form['source'],'size':form['size'],'lines':form['lines']})
out = '$PROJECT_DIR/fdo88_forms.js'
with open(out,'w') as f:
    f.write('window.__FDO88_FORMS = ')
    json.dump(by_tool, f)
    f.write(';\n')
print(f'  fdo88_forms.js: {os.path.getsize(out)/1024/1024:.1f} MB ({len(by_tool)} tools, {sum(len(v) for v in by_tool.values())} forms)')
"
    fi
fi

echo ""
echo "=================================================="
echo "  Pipeline complete!"
echo "=================================================="
echo "  Open index.html in a browser to view the site."
echo "=================================================="
