package com.btl.telcochurn.controller;

import com.btl.telcochurn.dto.DashboardSummaryResponse;
import com.btl.telcochurn.dto.DashboardDetailsResponse;
import com.btl.telcochurn.service.DashboardService;
import org.springframework.core.io.Resource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/summary")
    public DashboardSummaryResponse getSummary() {
        return dashboardService.readSummary();
    }

    @GetMapping("/details")
    public DashboardDetailsResponse getDetails() {
        return dashboardService.readDetails();
    }

    @GetMapping(value = "/charts/{fileName}", produces = MediaType.IMAGE_PNG_VALUE)
    public ResponseEntity<Resource> getChart(@PathVariable String fileName) {
        return ResponseEntity.ok(dashboardService.loadChart(fileName));
    }
}
