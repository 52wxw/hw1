package com.inspect.repository;

import com.inspect.model.OperationLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface OperationLogRepository extends JpaRepository<OperationLog, Integer> {
    List<OperationLog> findByUserIdOrderByOpTimeDesc(Integer userId);
    List<OperationLog> findByDeviceIdOrderByOpTimeDesc(Integer deviceId);
}

