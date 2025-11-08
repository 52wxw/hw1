package com.inspect.repository;

import com.inspect.model.Device;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * 设备数据访问接口
 * 文件名与类名一致（DeviceRepository.java → DeviceRepository），解决类名不匹配错误
 */
@Repository // 标识为数据访问组件
// 继承JpaRepository，自动获得CRUD方法（save/findAll/findById等）
public interface DeviceRepository extends JpaRepository<Device, Integer> {
    // 无需额外方法，JpaRepository已包含基础操作
}
