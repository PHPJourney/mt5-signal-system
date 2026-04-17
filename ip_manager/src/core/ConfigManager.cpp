#include "ConfigManager.h"
#include "src/utils/Logger.h"
#include <QStandardPaths>
#include <QDir>

ConfigManager::ConfigManager(QObject *parent)
    : QObject(parent), m_settings(nullptr)
{
    m_configPath = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) 
                   + "/config.ini";
    
    QDir().mkpath(QFileInfo(m_configPath).absolutePath());
    
    m_settings = new QSettings(m_configPath, QSettings::IniFormat, this);
}

ConfigManager::~ConfigManager()
{
    if (m_settings) {
        delete m_settings;
    }
}

ConfigManager& ConfigManager::instance()
{
    static ConfigManager instance;
    return instance;
}

bool ConfigManager::load()
{
    QMutexLocker locker(&m_mutex);
    
    if (!m_settings->contains("AI/Provider")) {
        // 首次运行，设置默认值
        m_settings->setValue("AI/Provider", "openai");
        m_settings->setValue("AI/Model", "gpt-4");
        m_settings->setValue("Language", "zh_CN");
        m_settings->setValue("Theme", "light");
        m_settings->setValue("DefaultCountry", "china");
        
        // 默认费用
        m_settings->setValue("Fees/SoftwareCopyright/china", 300);
        m_settings->setValue("Fees/SoftwareCopyright/usa", 120);
        m_settings->setValue("Fees/SoftwareCopyright/europe", 150);
        
        m_settings->setValue("Fees/Trademark/china", 270);
        m_settings->setValue("Fees/Trademark/usa", 350);
        m_settings->setValue("Fees/Trademark/europe", 850);
        
        m_settings->setValue("Fees/Patent/invention_china", 900);
        m_settings->setValue("Fees/Patent/utility_china", 500);
        m_settings->setValue("Fees/Patent/design_china", 500);
        
        save();
        LOG_INFO("配置文件创建完成（默认值）: " + m_configPath);
    } else {
        LOG_INFO("配置文件加载成功: " + m_configPath);
    }
    
    return true;
}

bool ConfigManager::save()
{
    QMutexLocker locker(&m_mutex);
    m_settings->sync();
    return true;
}

QString ConfigManager::getAIProvider() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("AI/Provider", "openai").toString();
}

void ConfigManager::setAIProvider(const QString& provider)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("AI/Provider", provider);
}

QString ConfigManager::getAIKey() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("AI/Key", "").toString();
}

void ConfigManager::setAIKey(const QString& key)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("AI/Key", key);
}

QString ConfigManager::getAIModel() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("AI/Model", "gpt-4").toString();
}

void ConfigManager::setAIModel(const QString& model)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("AI/Model", model);
}

QString ConfigManager::getAlipayAppId() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("Payment/AlipayAppId", "").toString();
}

void ConfigManager::setAlipayAppId(const QString& appId)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("Payment/AlipayAppId", appId);
}

QString ConfigManager::getWechatAppId() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("Payment/WechatAppId", "").toString();
}

void ConfigManager::setWechatAppId(const QString& appId)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("Payment/WechatAppId", appId);
}

double ConfigManager::getSoftwareCopyrightFee(const QString& country) const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("Fees/SoftwareCopyright/" + country, 300).toDouble();
}

void ConfigManager::setSoftwareCopyrightFee(const QString& country, double fee)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("Fees/SoftwareCopyright/" + country, fee);
}

double ConfigManager::getTrademarkFee(const QString& country) const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("Fees/Trademark/" + country, 270).toDouble();
}

void ConfigManager::setTrademarkFee(const QString& country, double fee)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("Fees/Trademark/" + country, fee);
}

double ConfigManager::getPatentFee(const QString& type, const QString& country) const
{
    QString key = "Fees/Patent/" + type + "_" + country;
    QMutexLocker locker(&m_mutex);
    return m_settings->value(key, 500).toDouble();
}

void ConfigManager::setPatentFee(const QString& type, const QString& country, double fee)
{
    QString key = "Fees/Patent/" + type + "_" + country;
    QMutexLocker locker(&m_mutex);
    m_settings->setValue(key, fee);
}

QString ConfigManager::getLanguage() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("Language", "zh_CN").toString();
}

void ConfigManager::setLanguage(const QString& lang)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("Language", lang);
}

QString ConfigManager::getTheme() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("Theme", "light").toString();
}

void ConfigManager::setTheme(const QString& theme)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("Theme", theme);
}

QString ConfigManager::getDefaultCountry() const
{
    QMutexLocker locker(&m_mutex);
    return m_settings->value("DefaultCountry", "china").toString();
}

void ConfigManager::setDefaultCountry(const QString& country)
{
    QMutexLocker locker(&m_mutex);
    m_settings->setValue("DefaultCountry", country);
}

QString ConfigManager::getConfigPath() const
{
    return m_configPath;
}