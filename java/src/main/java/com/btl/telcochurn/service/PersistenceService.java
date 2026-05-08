package com.btl.telcochurn.service;

import com.btl.telcochurn.dto.PredictionRequest;
import com.btl.telcochurn.dto.PredictionResponse;
import com.btl.telcochurn.entity.CustomerRecord;
import com.btl.telcochurn.entity.PredictionRecord;
import com.btl.telcochurn.entity.TrainingRunRecord;
import com.btl.telcochurn.repository.CustomerRecordRepository;
import com.btl.telcochurn.repository.PredictionRecordRepository;
import com.btl.telcochurn.repository.TrainingRunRecordRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeParseException;
import java.util.Map;

@Service
public class PersistenceService {

    private final CustomerRecordRepository customerRecordRepository;
    private final PredictionRecordRepository predictionRecordRepository;
    private final TrainingRunRecordRepository trainingRunRecordRepository;
    private final ObjectMapper objectMapper;

    public PersistenceService(
            CustomerRecordRepository customerRecordRepository,
            PredictionRecordRepository predictionRecordRepository,
            TrainingRunRecordRepository trainingRunRecordRepository,
            ObjectMapper objectMapper
    ) {
        this.customerRecordRepository = customerRecordRepository;
        this.predictionRecordRepository = predictionRecordRepository;
        this.trainingRunRecordRepository = trainingRunRecordRepository;
        this.objectMapper = objectMapper;
    }

    public void savePrediction(PredictionRequest request, PredictionResponse response) {
        CustomerRecord customerRecord = new CustomerRecord();
        customerRecord.setExternalCustomerId(extractCustomerId(request.customer()));
        customerRecord.setCustomerPayload(writeJson(request.customer()));
        customerRecord.setCreatedAt(LocalDateTime.now());
        customerRecord = customerRecordRepository.save(customerRecord);

        PredictionRecord predictionRecord = new PredictionRecord();
        predictionRecord.setCustomer(customerRecord);
        predictionRecord.setModelName(response.model());
        predictionRecord.setPredictionLabel(response.prediction());
        predictionRecord.setChurnProbability(response.churnProbability());
        predictionRecord.setPredictedAt(parseDateTime(response.predictedAt()));
        predictionRecordRepository.save(predictionRecord);
    }

    public void saveTrainingRun(JsonNode summaryNode, String summaryPath, String dashboardPath, String rawOutput) {
        JsonNode metrics = summaryNode.path("metrics");

        TrainingRunRecord record = new TrainingRunRecord();
        record.setStatus("trained");
        record.setBestModel(summaryNode.path("best_model").asText(null));
        record.setDatasetRows(readNullableInt(summaryNode, "dataset_rows"));
        record.setFeatureColumns(readNullableInt(summaryNode, "feature_columns"));
        record.setAccuracyScore(readNullableDouble(metrics, "accuracy"));
        record.setPrecisionScore(readNullableDouble(metrics, "precision"));
        record.setRecallScore(readNullableDouble(metrics, "recall"));
        record.setF1Score(readNullableDouble(metrics, "f1"));
        record.setRocAucScore(readNullableDouble(metrics, "roc_auc"));
        record.setSummaryPath(summaryPath);
        record.setDashboardPath(dashboardPath);
        record.setRawOutput(rawOutput);
        record.setCreatedAt(LocalDateTime.now());
        trainingRunRecordRepository.save(record);
    }

    private String extractCustomerId(Map<String, Object> customer) {
        Object rawId = customer.get("CustomerID");
        return rawId == null ? null : String.valueOf(rawId);
    }

    private String writeJson(Object payload) {
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Cannot serialize payload for persistence", ex);
        }
    }

    private LocalDateTime parseDateTime(String value) {
        if (value == null || value.isBlank()) {
            return LocalDateTime.now();
        }
        try {
            return LocalDateTime.parse(value);
        } catch (DateTimeParseException ex) {
            return LocalDateTime.now();
        }
    }

    private Integer readNullableInt(JsonNode node, String fieldName) {
        return node.hasNonNull(fieldName) ? node.path(fieldName).asInt() : null;
    }

    private Double readNullableDouble(JsonNode node, String fieldName) {
        return node.hasNonNull(fieldName) ? node.path(fieldName).asDouble() : null;
    }
}
