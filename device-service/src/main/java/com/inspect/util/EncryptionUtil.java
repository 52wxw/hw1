package com.inspect.util;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;

/**
 * 密码加密解密工具（AES算法）
 */
@Component
public class EncryptionUtil {

    @Value("${encrypt.key}")
    private String secretKey;

    private static final String ALGORITHM = "AES";
    // 明确加密模式（避免默认模式兼容问题）
    private static final String CIPHER_MODE = "AES/ECB/PKCS5Padding";
    // 统一编码格式
    private static final String CHARSET = "UTF-8";

    /**
     * 加密数据（设备密码专用）
     */
    public String encrypt(String data) {
        try {
            // 验证密钥长度（避免配置错误）
            int keyLength = secretKey.getBytes(CHARSET).length;
            if (keyLength != 16 && keyLength != 24 && keyLength != 32) {
                throw new IllegalArgumentException("AES密钥长度必须为16/24/32字节");
            }

            SecretKeySpec key = new SecretKeySpec(secretKey.getBytes(CHARSET), ALGORITHM);
            Cipher cipher = Cipher.getInstance(CIPHER_MODE);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            byte[] encrypted = cipher.doFinal(data.getBytes(CHARSET));
            return Base64.getEncoder().encodeToString(encrypted);
        } catch (Exception e) {
            throw new RuntimeException("加密失败：" + e.getMessage());
        }
    }

    /**
     * 解密数据（设备密码专用）
     */
    public String decrypt(String encryptedData) {
        try {
            SecretKeySpec key = new SecretKeySpec(secretKey.getBytes(CHARSET), ALGORITHM);
            Cipher cipher = Cipher.getInstance(CIPHER_MODE);
            cipher.init(Cipher.DECRYPT_MODE, key);
            byte[] decrypted = cipher.doFinal(Base64.getDecoder().decode(encryptedData));
            return new String(decrypted, CHARSET);
        } catch (Exception e) {
            throw new RuntimeException("解密失败：" + e.getMessage());
        }
    }
}
