package com.inspect.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TopologyLinkDto {
    private Integer sourceDeviceId;
    private String sourceName;
    private String sourceIp;
    private String sourcePort;
    private Integer targetDeviceId;
    private String targetName;
    private String targetIp;
    private String targetPort;
    private String status;
}


