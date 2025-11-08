package com.inspect.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TopologyResponse {
    private List<TopologyNodeDto> nodes;
    private List<TopologyLinkDto> links;
}


