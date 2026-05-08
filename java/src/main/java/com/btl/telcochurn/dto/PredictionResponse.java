package com.btl.telcochurn.dto;

public record PredictionResponse(
        String model,
        String prediction,
        double churnProbability,
        String predictedAt
) {
}
