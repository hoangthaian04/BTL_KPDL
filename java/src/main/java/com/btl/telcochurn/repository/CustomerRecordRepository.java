package com.btl.telcochurn.repository;

import com.btl.telcochurn.entity.CustomerRecord;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CustomerRecordRepository extends JpaRepository<CustomerRecord, Long> {
}
