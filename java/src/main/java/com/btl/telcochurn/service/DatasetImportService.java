package com.btl.telcochurn.service;

import com.btl.telcochurn.dto.DatasetImportResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Set;

@Service
public class DatasetImportService {

    private static final Set<String> SUPPORTED_EXTENSIONS = Set.of(".csv", ".xlsx", ".xlsm");

    private final ObjectMapper objectMapper;
    private final String pythonExecutable;
    private final String pythonAppPath;
    private final Path tempDir;

    public DatasetImportService(
            ObjectMapper objectMapper,
            @Value("${mining.python-executable}") String pythonExecutable,
            @Value("${mining.python-app-path}") String pythonAppPath,
            @Value("${mining.temp-dir}") String tempDir
    ) {
        this.objectMapper = objectMapper;
        this.pythonExecutable = pythonExecutable;
        this.pythonAppPath = pythonAppPath;
        this.tempDir = Path.of(tempDir);
    }

    public DatasetImportResponse importFile(MultipartFile file) {
        validateUpload(file);

        try {
            Files.createDirectories(tempDir);
            String originalName = file.getOriginalFilename() == null ? "dataset-upload.xlsx" : file.getOriginalFilename();
            String suffix = extractExtension(originalName);
            Path payloadPath = Files.createTempFile(tempDir, "dataset-import-", suffix);
            Files.copy(file.getInputStream(), payloadPath, StandardCopyOption.REPLACE_EXISTING);

            try {
                Process process = new ProcessBuilder(
                        pythonExecutable,
                        pythonAppPath,
                        "import-data",
                        "--input-file",
                        payloadPath.toString()
                ).redirectErrorStream(true).start();

                StringBuilder output = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        output.append(line);
                    }
                }

                int exitCode = process.waitFor();
                if (exitCode != 0) {
                    throw new IllegalStateException("Python import failed: " + output);
                }

                JsonNode root = objectMapper.readTree(output.toString());
                return new DatasetImportResponse(
                        "imported",
                        originalName,
                        root.path("dataset_path").asText(),
                        root.path("rows_before").asInt(),
                        root.path("incoming_rows").asInt(),
                        root.path("imported_rows").asInt(),
                        root.path("skipped_rows").asInt(),
                        root.path("duplicate_rows_removed").asInt(),
                        root.path("rows_after").asInt()
                );
            } finally {
                Files.deleteIfExists(payloadPath);
            }
        } catch (IOException ex) {
            throw new IllegalStateException("Dataset import failed", ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Dataset import interrupted", ex);
        }
    }

    private void validateUpload(MultipartFile file) {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("Uploaded file is empty");
        }
        String originalName = file.getOriginalFilename();
        if (originalName == null || originalName.isBlank()) {
            throw new IllegalArgumentException("Uploaded file name is missing");
        }
        String extension = extractExtension(originalName);
        if (!SUPPORTED_EXTENSIONS.contains(extension.toLowerCase())) {
            throw new IllegalArgumentException("Unsupported file type: " + extension);
        }
    }

    private String extractExtension(String fileName) {
        int dotIndex = fileName.lastIndexOf('.');
        return dotIndex >= 0 ? fileName.substring(dotIndex) : "";
    }
}
