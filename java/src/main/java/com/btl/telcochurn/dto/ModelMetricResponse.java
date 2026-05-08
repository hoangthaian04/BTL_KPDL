package com.btl.telcochurn.dto;

public record ModelMetricResponse(
        String model,
        double accuracy,
        double precision,
        double recall,
        double f1,
        double rocAuc
) {
}
