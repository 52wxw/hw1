package com.inspect.model;

import lombok.Data;

/**
 * 手动巡检请求体
 */
@Data
public class InspectRequest {
    /**
     * 巡检场景描述，例如：手动巡检/定时巡检
     */
    private String scenario = "手动巡检";

    /**
     * 是否开启自动修复
     */
    private Boolean autoRepair = Boolean.FALSE;
}


