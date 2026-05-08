package com.btl.telcochurn.dto;

public record TrainingResponse(
        String status,
        String bestModel,
        String summaryPath,
        String dashboardPath
) {
}
