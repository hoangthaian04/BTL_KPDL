package com.btl.telcochurn.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record PredictionResponse(
        String model,
        String prediction,
        @JsonProperty("churn_probability") double churnProbability,
        @JsonProperty("predicted_at") String predictedAt
) {
}
