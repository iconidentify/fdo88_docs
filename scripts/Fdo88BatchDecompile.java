import com.atomforge.fdo.fdo88.Fdo88Decompiler;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/**
 * Batch decompiles all .fdo88 binary files in a directory tree into
 * human-readable FDO88 source text using atomforge-fdo-java.
 *
 * Usage: java -cp atomforge-fdo.jar:. Fdo88BatchDecompile <input_dir> <output_dir>
 *
 * Reads every .fdo88 file, runs Fdo88Decompiler, writes .fdo text output.
 * Also produces a manifest.json with metadata for the web viewer.
 */
public class Fdo88BatchDecompile {

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: java Fdo88BatchDecompile <input_dir> <output_dir>");
            System.exit(1);
        }

        Path inputDir = Paths.get(args[0]);
        Path outputDir = Paths.get(args[1]);
        Files.createDirectories(outputDir);

        Fdo88Decompiler decompiler = Fdo88Decompiler.create();
        int success = 0, failed = 0;

        // Collect all results for manifest
        StringBuilder manifestJson = new StringBuilder();
        manifestJson.append("{\n  \"forms\": [\n");
        boolean first = true;

        // Walk all .fdo88 files
        List<Path> files = new ArrayList<>();
        Files.walk(inputDir)
            .filter(p -> p.toString().endsWith(".fdo88"))
            .sorted()
            .forEach(files::add);

        System.out.println("Decompiling " + files.size() + " FDO88 forms...");

        for (Path file : files) {
            String filename = file.getFileName().toString();
            String baseName = filename.replace(".fdo88", "");

            // Extract tool name and DB type from filename pattern: ToolName_DB14_123.fdo88
            String toolName = "";
            String dbType = "";
            String recordId = "";
            int lastUnderscore = baseName.lastIndexOf('_');
            if (lastUnderscore > 0) {
                recordId = baseName.substring(lastUnderscore + 1);
                String rest = baseName.substring(0, lastUnderscore);
                int secondLast = rest.lastIndexOf('_');
                if (secondLast > 0) {
                    dbType = rest.substring(secondLast + 1);
                    toolName = rest.substring(0, secondLast);
                }
            }

            try {
                byte[] binary = Files.readAllBytes(file);
                String text = decompiler.decompile(binary);

                // Create tool subdirectory in output
                Path toolDir = outputDir.resolve(toolName.isEmpty() ? "unknown" : toolName);
                Files.createDirectories(toolDir);

                Path outFile = toolDir.resolve(baseName + ".fdo");
                Files.writeString(outFile, text);

                if (!first) manifestJson.append(",\n");
                first = false;
                manifestJson.append("    {\"tool\": ")
                    .append(jsonString(toolName))
                    .append(", \"db\": ").append(jsonString(dbType))
                    .append(", \"record\": ").append(jsonString(recordId))
                    .append(", \"file\": ").append(jsonString(toolName + "/" + baseName + ".fdo"))
                    .append(", \"source\": ").append(jsonString(text))
                    .append(", \"size\": ").append(binary.length)
                    .append(", \"lines\": ").append(text.split("\n").length)
                    .append("}");

                success++;
                if (success % 100 == 0) {
                    System.out.println("  " + success + " done...");
                }
            } catch (Exception e) {
                failed++;
                System.err.println("  FAIL: " + filename + " -> " + e.getMessage());
            }
        }

        manifestJson.append("\n  ],\n");
        manifestJson.append("  \"total\": ").append(success).append(",\n");
        manifestJson.append("  \"failed\": ").append(failed).append("\n");
        manifestJson.append("}\n");

        Files.writeString(outputDir.resolve("fdo88_manifest.json"), manifestJson.toString());

        System.out.println("\nDone: " + success + " decompiled, " + failed + " failed");
        System.out.println("Manifest: " + outputDir.resolve("fdo88_manifest.json"));
    }

    private static String jsonString(String s) {
        if (s == null) return "null";
        StringBuilder sb = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '\\' -> sb.append("\\\\");
                case '"' -> sb.append("\\\"");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
                }
            }
        }
        sb.append('"');
        return sb.toString();
    }
}
