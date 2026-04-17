#ifndef CONFIGMANAGER_H
#define CONFIGMANAGER_H

#include <QObject>
#include <QString>
#include <QSettings>
#include <QJsonObject>
#include <QMutex>

class ConfigManager : public QObject
{
    Q_OBJECT

public:
    static ConfigManager& instance();
    
    // 加载/保存配置
    bool load();
    bool save();
    
    // AI 配置
    QString getAIProvider() const;
    void setAIProvider(const QString& provider);
    QString getAIKey() const;
    void setAIKey(const QString& key);
    QString getAIModel() const;
    void setAIModel(const QString& model);
    
    // 支付配置
    QString getAlipayAppId() const;
    void setAlipayAppId(const QString& appId);
    QString getWechatAppId() const;
    void setWechatAppId(const QString& appId);
    
    // 费用配置
    double getSoftwareCopyrightFee(const QString& country) const;
    void setSoftwareCopyrightFee(const QString& country, double fee);
    double getTrademarkFee(const QString& country) const;
    void setTrademarkFee(const QString& country, double fee);
    double getPatentFee(const QString& type, const QString& country) const;
    void setPatentFee(const QString& type, const QString& country, double fee);
    
    // 通用配置
    QString getLanguage() const;
    void setLanguage(const QString& lang);
    QString getTheme() const;
    void setTheme(const QString& theme);
    QString getDefaultCountry() const;
    void setDefaultCountry(const QString& country);
    
    // 获取配置文件路径
    QString getConfigPath() const;

private:
    ConfigManager(QObject *parent = nullptr);
    ~ConfigManager();
    ConfigManager(const ConfigManager&) = delete;
    ConfigManager& operator=(const ConfigManager&) = delete;
    
    QString m_configPath;
    QSettings* m_settings;
    QMutex m_mutex;
};

#endif // CONFIGMANAGER_H