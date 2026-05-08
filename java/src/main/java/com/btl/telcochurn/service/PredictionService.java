package com.btl.telcochurn.service;

import com.btl.telcochurn.dto.PredictionRequest;
import com.btl.telcochurn.dto.PredictionResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
public class PredictionService {

    private final ObjectMapper objectMapper;
    private final String pythonExecutable;
    private final String pythonAppPath;
    private final Path tempDir;
    private final PersistenceService persistenceService;

    public PredictionService(
            ObjectMapper objectMapper,
            @Value("${mining.python-executable}") String pythonExecutable,
            @Value("${mining.python-app-path}") String pythonAppPath,
            @Value("${mining.temp-dir}") String tempDir,
            PersistenceService persistenceService
    ) {
        this.objectMapper = objectMapper;
        this.pythonExecutable = pythonExecutable;
        this.pythonAppPath = pythonAppPath;
        this.tempDir = Path.of(tempDir);
        this.persistenceService = persistenceService;
    }

    public PredictionResponse predict(PredictionRequest request) {
        try {
            Files.createDirectories(tempDir);
            Path payloadPath = Files.createTempFile(tempDir, "prediction-", ".json");
            objectMapper.writeValue(payloadPath.toFile(), request.customer());

            Process process = new ProcessBuilder(
                    pythonExecutable,
                    pythonAppPath,
                    "predict",
                    "--input-json",
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
                throw new IllegalStateException("Python prediction failed: " + output);
            }

            PredictionResponse response = objectMapper.readValue(output.toString(), PredictionResponse.class);
            appendCustomerToDataset(payloadPath);
            persistenceService.savePrediction(request, response);
            return response;
        } catch (IOException ex) {
            throw new IllegalStateException("Prediction pipeline failed", ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Prediction pipeline interrupted", ex);
        }
    }

    private void appendCustomerToDataset(Path payloadPath) throws IOException, InterruptedException {
        Process process = new ProcessBuilder(
                pythonExecutable,
                pythonAppPath,
                "append-customer",
                "--input-json",
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
            throw new IllegalStateException("Appending predicted customer failed: " + output);
        }
    }
}
