package com.btl.telcochurn.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

@Entity
@Table(name = "training_runs")
public class TrainingRunRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "status", nullable = false, length = 30)
    private String status;

    @Column(name = "best_model", length = 100)
    private String bestModel;

    @Column(name = "dataset_rows")
    private Integer datasetRows;

    @Column(name = "feature_columns")
    private Integer featureColumns;

    @Column(name = "accuracy_score")
    private Double accuracyScore;

    @Column(name = "precision_score")
    private Double precisionScore;

    @Column(name = "recall_score")
    private Double recallScore;

    @Column(name = "f1_score")
    private Double f1Score;

    @Column(name = "roc_auc_score")
    private Double rocAucScore;

    @Column(name = "summary_path", length = 255)
    private String summaryPath;

    @Column(name = "dashboard_path", length = 255)
    private String dashboardPath;

    @Lob
    @Column(name = "raw_output", columnDefinition = "LONGTEXT")
    private String rawOutput;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getBestModel() {
        return bestModel;
    }

    public void setBestModel(String bestModel) {
        this.bestModel = bestModel;
    }

    public Integer getDatasetRows() {
        return datasetRows;
    }

    public void setDatasetRows(Integer datasetRows) {
        this.datasetRows = datasetRows;
    }

    public Integer getFeatureColumns() {
        return featureColumns;
    }

    public void setFeatureColumns(Integer featureColumns) {
        this.featureColumns = featureColumns;
    }

    public Double getAccuracyScore() {
        return accuracyScore;
    }

    public void setAccuracyScore(Double accuracyScore) {
        this.accuracyScore = accuracyScore;
    }

    public Double getPrecisionScore() {
        return precisionScore;
    }

    public void setPrecisionScore(Double precisionScore) {
        this.precisionScore = precisionScore;
    }

    public Double getRecallScore() {
        return recallScore;
    }

    public void setRecallScore(Double recallScore) {
        this.recallScore = recallScore;
    }

    public Double getF1Score() {
        return f1Score;
    }

    public void setF1Score(Double f1Score) {
        this.f1Score = f1Score;
    }

    public Double getRocAucScore() {
        return rocAucScore;
    }

    public void setRocAucScore(Double rocAucScore) {
        this.rocAucScore = rocAucScore;
    }

    public String getSummaryPath() {
        return summaryPath;
    }

    public void setSummaryPath(String summaryPath) {
        this.summaryPath = summaryPath;
    }

    public String getDashboardPath() {
        return dashboardPath;
    }

    public void setDashboardPath(String dashboardPath) {
        this.dashboardPath = dashboardPath;
    }

    public String getRawOutput() {
        return rawOutput;
    }

    public void setRawOutput(String rawOutput) {
        this.rawOutput = rawOutput;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
