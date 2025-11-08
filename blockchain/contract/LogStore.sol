// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LogStore {
    struct OperationLog {
        string deviceId;
        string opType;
        string logHash;
        uint256 timestamp;
        string operator;
    }

    OperationLog[] public logs;
    mapping(string => uint256[]) public deviceLogIds;

    event LogUploaded(uint256 logId, string deviceId, string opType, uint256 timestamp);

    function uploadLog(string memory deviceId, string memory opType, string memory logHash, string memory operator) public {
        uint256 logId = logs.length;
        logs.push(OperationLog({
            deviceId: deviceId,
            opType: opType,
            logHash: logHash,
            timestamp: block.timestamp,
            operator: operator
        }));
        deviceLogIds[deviceId].push(logId);
        emit LogUploaded(logId, deviceId, opType, block.timestamp);
    }

    function getDeviceLogIds(string memory deviceId) public view returns (uint256[] memory) {
        return deviceLogIds[deviceId];
    }

    function getLog(uint256 logId) public view returns (OperationLog memory) {
        require(logId < logs.length, "Log does not exist");
        return logs[logId];
    }
}
