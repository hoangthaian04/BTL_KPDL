package com.btl.telcochurn.dto;

public record CustomerRiskResponse(
        String customerId,
        String contract,
        String internetService,
        String paymentMethod,
        String actualChurn,
        String predictedChurn,
        double churnProbability
) {
}
