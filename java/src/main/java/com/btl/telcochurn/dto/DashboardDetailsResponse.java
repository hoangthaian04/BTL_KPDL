package com.btl.telcochurn.dto;

import java.util.List;

public record DashboardDetailsResponse(
        DashboardSummaryResponse summary,
        List<ModelMetricResponse> modelMetrics,
        List<CustomerRiskResponse> highRiskCustomers,
        List<CustomerRiskResponse> careCustomers,
        List<ChartAssetResponse> charts,
        ChurnDistributionResponse churnDistribution
) {
}
