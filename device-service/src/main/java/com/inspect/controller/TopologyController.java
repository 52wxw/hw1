package com.inspect.controller;

import com.inspect.annotation.RequireRole;
import com.inspect.common.Result;
import com.inspect.dto.TopologyResponse;
import com.inspect.service.TopologyService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/topology")
public class TopologyController {

    @Autowired
    private TopologyService topologyService;

    @GetMapping
    @RequireRole("readonly")
    public Result<TopologyResponse> getTopology() {
        TopologyResponse response = topologyService.buildTopology();
        return Result.success(response);
    }
}


