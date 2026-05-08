package com.btl.telcochurn.dto;

public record ChurnDistributionResponse(
        int churnNo,
        int care,
        int churnYes
) {
}
