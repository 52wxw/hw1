package com.inspect.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TopologyNodeDto {
    private Integer id;
    private String name;
    private String ip;
    private String vendor;
    private String status;
    private double x;
    private double y;
    private double z;
}


