package com.inspect.service;

import com.inspect.dto.TopologyLinkDto;
import com.inspect.dto.TopologyNodeDto;
import com.inspect.dto.TopologyResponse;
import com.inspect.model.Device;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

@Service
public class TopologyService {

    private static final Logger log = LoggerFactory.getLogger(TopologyService.class);

    @Value("${services.collect:http://collect-service:8001}")
    private String collectServiceUrl;

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private RestTemplate restTemplate;

    @Value("${topology.cache.enabled:true}")
    private boolean cacheEnabled;

    @Value("${topology.cache.ttl:300}")
    private long cacheTtlSeconds;

    private final ReadWriteLock cacheLock = new ReentrantReadWriteLock();
    private volatile TopologyResponse cachedTopology;
    private volatile Instant cacheTimestamp;

    public TopologyResponse buildTopology() {
        if (!cacheEnabled) {
            return buildTopologyInternal();
        }

        TopologyResponse cached = getCachedIfFresh();
        if (cached != null) {
            return cached;
        }

        return refreshCache();
    }

    private TopologyResponse getCachedIfFresh() {
        cacheLock.readLock().lock();
        try {
            if (cachedTopology == null || cacheTimestamp == null) {
                return null;
            }
            Duration age = Duration.between(cacheTimestamp, Instant.now());
            if (age.isNegative()) {
                return null;
            }
            Duration ttl = Duration.ofSeconds(cacheTtlSeconds);
            if (age.compareTo(ttl) > 0) {
                return null;
            }
            return cachedTopology;
        } finally {
            cacheLock.readLock().unlock();
        }
    }

    private TopologyResponse refreshCache() {
        cacheLock.writeLock().lock();
        try {
            TopologyResponse fresh = buildTopologyInternal();
            cachedTopology = fresh;
            cacheTimestamp = Instant.now();
            return fresh;
        } catch (Exception ex) {
            log.warn("Refresh topology cache failed, keep last snapshot if available", ex);
            return cachedTopology;
        } finally {
            cacheLock.writeLock().unlock();
        }
    }

    @Scheduled(fixedDelayString = "${topology.cache.refresh-interval:300000}")
    public void scheduledRefresh() {
        if (!cacheEnabled) {
            return;
        }
        refreshCache();
    }

    private TopologyResponse buildTopologyInternal() {
        List<Device> devices = deviceService.findAll();
        if (devices.isEmpty()) {
            return new TopologyResponse(Collections.emptyList(), Collections.emptyList());
        }

        Map<Integer, Device> deviceMap = new HashMap<>();
        for (Device device : devices) {
            deviceMap.put(device.getId(), device);
        }

        List<Map<String, Object>> rawLinks = new ArrayList<>();

        for (Device device : devices) {
            String password = deviceService.getDecryptedPassword(device.getId());
            if (password == null) {
                continue;
            }
            try {
                Map<String, Object> payload = new HashMap<>();
                payload.put("device_id", device.getId());
                payload.put("ip", device.getIp());
                payload.put("username", device.getUsername());
                payload.put("password", password);
                payload.put("vendor", device.getVendor());
                payload.put("protocol", device.getProtocol() != null ? device.getProtocol() : "ssh");
                payload.put("device_name", device.getName());

                ResponseEntity<Map> response = restTemplate.postForEntity(
                    collectServiceUrl + "/api/topology/lldp",
                    payload,
                    Map.class
                );
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    Object data = response.getBody().get("data");
                    if (data instanceof Map) {
                        Object linksObj = ((Map<?, ?>) data).get("links");
                        if (linksObj instanceof List) {
                            for (Object item : (List<?>) linksObj) {
                                if (item instanceof Map) {
                                    rawLinks.add((Map<String, Object>) item);
                                }
                            }
                        }
                    }
                }
            } catch (Exception ex) {
                log.debug("LLDP collection failed for device {}({}): {}", device.getName(), device.getIp(), ex.getMessage());
            }
        }

        List<TopologyLinkDto> mergedLinks = mergeLinks(rawLinks, deviceMap);
        List<TopologyNodeDto> nodes = layoutNodes(devices);
        return new TopologyResponse(
            Collections.unmodifiableList(new ArrayList<>(nodes)),
            Collections.unmodifiableList(new ArrayList<>(mergedLinks))
        );
    }

    private List<TopologyNodeDto> layoutNodes(List<Device> devices) {
        int n = devices.size();
        double radius = Math.max(10, n * 2);
        List<TopologyNodeDto> nodes = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            Device device = devices.get(i);
            double angle = (2 * Math.PI * i) / n;
            double x = radius * Math.cos(angle);
            double z = radius * Math.sin(angle);
            double y = 0;

            nodes.add(new TopologyNodeDto(
                device.getId(),
                device.getName(),
                device.getIp(),
                device.getVendor(),
                device.getStatus(),
                x,
                y,
                z
            ));
        }

        return nodes;
    }

    private List<TopologyLinkDto> mergeLinks(List<Map<String, Object>> rawLinks, Map<Integer, Device> deviceMap) {
        Map<String, TopologyLinkDto> merged = new HashMap<>();

        for (Map<String, Object> link : rawLinks) {
            Integer deviceId = toInt(link.get("device_id"));
            String deviceName = stringify(link.get("device_name"));
            String localPort = stringify(link.get("local_port"));
            String neighbor = stringify(link.get("neighbor"));
            String neighborPort = stringify(link.get("neighbor_port"));
            String status = stringify(link.get("status"));

            Device sourceDevice = deviceId != null ? deviceMap.get(deviceId) : null;
            Device targetDevice = findDeviceByNameOrIp(deviceMap.values(), neighbor);

            if (sourceDevice == null || localPort == null || neighbor == null) {
                continue;
            }

            Integer targetId = targetDevice != null ? targetDevice.getId() : null;
            String targetIp = targetDevice != null ? targetDevice.getIp() : neighbor;

            String key = buildLinkKey(sourceDevice.getName(), localPort, neighbor, neighborPort);

            TopologyLinkDto existing = merged.get(key);
            if (existing == null) {
                merged.put(key, new TopologyLinkDto(
                    sourceDevice.getId(),
                    sourceDevice.getName(),
                    sourceDevice.getIp(),
                    localPort,
                    targetId,
                    neighbor,
                    targetIp,
                    neighborPort,
                    status != null ? status : "Unknown"
                ));
            } else {
                if ("Up".equalsIgnoreCase(existing.getStatus()) || status == null) {
                    continue;
                }
                existing.setStatus(status);
            }
        }

        return new ArrayList<>(merged.values());
    }

    private String buildLinkKey(String sourceName, String sourcePort, String targetName, String targetPort) {
        List<String> parts = Arrays.asList(
            sourceName + "#" + sourcePort,
            targetName + "#" + targetPort
        );
        Collections.sort(parts);
        return String.join("|", parts);
    }

    private static String stringify(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private static Integer toInt(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Device findDeviceByNameOrIp(Collection<Device> devices, String neighbor) {
        if (neighbor == null) {
            return null;
        }
        for (Device device : devices) {
            if (neighbor.equalsIgnoreCase(device.getName()) || neighbor.equals(device.getIp())) {
                return device;
            }
        }
        return null;
    }
}


