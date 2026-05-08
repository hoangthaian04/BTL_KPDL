package com.btl.telcochurn.service;

import com.btl.telcochurn.dto.TrainingResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;

@Service
public class TrainingService {

    private final ObjectMapper objectMapper;
    private final String pythonExecutable;
    private final String pythonAppPath;
    private final Path summaryPath;
    private final Path dashboardPath;
    private final PersistenceService persistenceService;

    public TrainingService(
            ObjectMapper objectMapper,
            @Value("${mining.python-executable}") String pythonExecutable,
            @Value("${mining.python-app-path}") String pythonAppPath,
            @Value("${mining.summary-path}") String summaryPath,
            @Value("${mining.dashboard-path}") String dashboardPath,
            PersistenceService persistenceService
    ) {
        this.objectMapper = objectMapper;
        this.pythonExecutable = pythonExecutable;
        this.pythonAppPath = pythonAppPath;
        this.summaryPath = Path.of(summaryPath);
        this.dashboardPath = Path.of(dashboardPath);
        this.persistenceService = persistenceService;
    }

    public TrainingResponse train() {
        try {
            Process process = new ProcessBuilder(
                    pythonExecutable,
                    pythonAppPath,
                    "train"
            ).redirectErrorStream(true).start();

            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append(System.lineSeparator());
                }
            }

            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new IllegalStateException("Python training failed: " + output);
            }

            JsonNode root = objectMapper.readTree(summaryPath.toFile());
            persistenceService.saveTrainingRun(root, summaryPath.toString(), dashboardPath.toString(), output.toString());
            return new TrainingResponse(
                    "trained",
                    root.path("best_model").asText(),
                    summaryPath.toString(),
                    dashboardPath.toString()
            );
        } catch (IOException ex) {
            throw new IllegalStateException("Training pipeline failed", ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Training pipeline interrupted", ex);
        }
    }
}
