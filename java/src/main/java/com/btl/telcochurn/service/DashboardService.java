package com.btl.telcochurn.service;

import com.btl.telcochurn.dto.ChartAssetResponse;
import com.btl.telcochurn.dto.ChurnDistributionResponse;
import com.btl.telcochurn.dto.CustomerRiskResponse;
import com.btl.telcochurn.dto.DashboardDetailsResponse;
import com.btl.telcochurn.dto.DashboardSummaryResponse;
import com.btl.telcochurn.dto.ModelMetricResponse;
import com.btl.telcochurn.dto.SmoteStageResponse;
import com.btl.telcochurn.dto.SmoteSummaryResponse;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.PathResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class DashboardService {

    private final ObjectMapper objectMapper;
    private final Path summaryPath;
    private final Path dashboardPath;
    private final Path metricsPath;
    private final Path highRiskPath;
    private final Path carePath;
    private final Path chartsPath;

    public DashboardService(
            ObjectMapper objectMapper,
            @Value("${mining.summary-path}") String summaryPath,
            @Value("${mining.dashboard-path}") String dashboardPath,
            @Value("${mining.metrics-path}") String metricsPath,
            @Value("${mining.high-risk-path}") String highRiskPath,
            @Value("${mining.care-path}") String carePath,
            @Value("${mining.charts-path}") String chartsPath
    ) {
        this.objectMapper = objectMapper;
        this.summaryPath = Path.of(summaryPath);
        this.dashboardPath = Path.of(dashboardPath);
        this.metricsPath = Path.of(metricsPath);
        this.highRiskPath = Path.of(highRiskPath);
        this.carePath = Path.of(carePath);
        this.chartsPath = Path.of(chartsPath);
    }

    public DashboardSummaryResponse readSummary() {
        try {
            JsonNode root = objectMapper.readTree(summaryPath.toFile());
            return mapSummary(root);
        } catch (IOException ex) {
            throw new IllegalStateException("Cannot read training summary from Python artifacts", ex);
        }
    }

    public DashboardDetailsResponse readDetails() {
        try {
            JsonNode summaryNode = objectMapper.readTree(summaryPath.toFile());
            DashboardSummaryResponse summary = mapSummary(summaryNode);
            return new DashboardDetailsResponse(
                    summary,
                    readModelMetrics(),
                    readRiskCustomers(highRiskPath),
                    readRiskCustomers(carePath),
                    readCharts(),
                    new ChurnDistributionResponse(
                            summaryNode.path("prediction_label_distribution").path("Churn No").asInt(),
                            summaryNode.path("prediction_label_distribution").path("Can cham soc").asInt(),
                            summaryNode.path("prediction_label_distribution").path("Churn Yes").asInt()
                    )
            );
        } catch (IOException ex) {
            throw new IllegalStateException("Cannot read dashboard details from Python artifacts", ex);
        }
    }

    public Resource loadChart(String fileName) {
        Path chartFile = chartsPath.resolve(fileName).normalize();
        if (!chartFile.startsWith(chartsPath) || !Files.exists(chartFile)) {
            throw new IllegalArgumentException("Chart not found: " + fileName);
        }
        return new PathResource(chartFile);
    }

    private DashboardSummaryResponse mapSummary(JsonNode root) {
        JsonNode metrics = root.path("metrics");
        return new DashboardSummaryResponse(
                root.path("dataset_rows").asInt(),
                root.path("feature_columns").asInt(),
                root.path("train_rows_before_smote").asInt(),
                root.path("balanced_train_rows").asInt(),
                root.path("best_model").asText(),
                metrics.path("accuracy").asDouble(),
                metrics.path("precision").asDouble(),
                metrics.path("recall").asDouble(),
                metrics.path("f1").asDouble(),
                metrics.path("roc_auc").asDouble(),
                new SmoteSummaryResponse(
                        new SmoteStageResponse(
                                root.path("smote_summary").path("before").path("churn_no").asInt(),
                                root.path("smote_summary").path("before").path("churn_yes").asInt(),
                                root.path("smote_summary").path("before").path("total").asInt()
                        ),
                        new SmoteStageResponse(
                                root.path("smote_summary").path("after").path("churn_no").asInt(),
                                root.path("smote_summary").path("after").path("churn_yes").asInt(),
                                root.path("smote_summary").path("after").path("total").asInt()
                        )
                ),
                dashboardPath.toString()
        );
    }

    private List<ModelMetricResponse> readModelMetrics() throws IOException {
        List<ModelMetricResponse> rows = new ArrayList<>();
        try (BufferedReader reader = Files.newBufferedReader(metricsPath, StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            if (header == null) {
                return rows;
            }
            String line;
            while ((line = reader.readLine()) != null) {
                String[] values = line.split(",", -1);
                if (values.length < 6) {
                    continue;
                }
                rows.add(new ModelMetricResponse(
                        values[0],
                        parseDouble(values[1]),
                        parseDouble(values[2]),
                        parseDouble(values[3]),
                        parseDouble(values[4]),
                        parseDouble(values[5])
                ));
            }
        }
        return rows;
    }

    private List<CustomerRiskResponse> readRiskCustomers(Path sourcePath) throws IOException {
        List<CustomerRiskResponse> rows = new ArrayList<>();
        if (!Files.exists(sourcePath)) {
            return rows;
        }
        try (BufferedReader reader = Files.newBufferedReader(sourcePath, StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            if (header == null) {
                return rows;
            }
            String[] headers = header.split(",", -1);
            String line;
            while ((line = reader.readLine()) != null && rows.size() < 10) {
                String[] values = line.split(",", -1);
                Map<String, String> row = zip(headers, values);
                double probability = parseDouble(row.getOrDefault("Churn Probability", "0"));
                rows.add(new CustomerRiskResponse(
                        row.getOrDefault("CustomerID", ""),
                        row.getOrDefault("Contract", ""),
                        row.getOrDefault("Internet Service", ""),
                        row.getOrDefault("Payment Method", ""),
                        row.getOrDefault("Actual Churn", ""),
                        classifyPrediction(probability),
                        probability
                ));
            }
        }
        return rows;
    }

    private List<ChartAssetResponse> readCharts() throws IOException {
        List<ChartAssetResponse> charts = new ArrayList<>();
        if (!Files.exists(chartsPath)) {
            return charts;
        }
        Map<String, String> titles = Map.of(
                "churn_distribution.png", "Churn Distribution",
                "model_comparison_f1.png", "Model Comparison by F1",
                "confusion_matrix.png", "Confusion Matrix",
                "feature_importance.png", "Feature Importance"
        );
        Files.list(chartsPath)
                .filter(Files::isRegularFile)
                .forEach(path -> charts.add(new ChartAssetResponse(
                        path.getFileName().toString().replace(".png", ""),
                        titles.getOrDefault(path.getFileName().toString(), path.getFileName().toString()),
                        "/api/dashboard/charts/" + path.getFileName()
                )));
        return charts;
    }

    private Map<String, String> zip(String[] headers, String[] values) {
        java.util.Map<String, String> row = new java.util.LinkedHashMap<>();
        for (int index = 0; index < headers.length; index++) {
            row.put(headers[index], index < values.length ? values[index] : "");
        }
        return objectMapper.convertValue(row, new TypeReference<Map<String, String>>() {});
    }

    private double parseDouble(String value) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException ex) {
            return 0.0;
        }
    }

    private String classifyPrediction(double probability) {
        if (probability > 0.5 && probability < 0.8) {
            return "Can cham soc";
        }
        if (probability >= 0.8) {
            return "Churn Yes";
        }
        return "Churn No";
    }
}
