#include "ProgressTracker.h"
#include "src/utils/Logger.h"

ProgressTracker::ProgressTracker(QObject *parent)
    : QObject(parent),
      m_cnipaTracker(new CNIPATracker(this)),
      m_usptoTracker(new USPTOTracker(this))
{
    LOG_INFO("进度追踪器初始化完成");
}

void ProgressTracker::setAPIConfig(const QJsonObject& config)
{
    m_apiConfig = config;
    LOG_INFO("API 配置已更新");
}

TrackingResult ProgressTracker::trackByCountry(const QString& country, const QString& trackingNumber, const QString& appType)
{
    LOG_INFO("追踪申请进度: 国家=" + country + " 申请号=" + trackingNumber + " 类型=" + appType);
    
    TrackingResult result;
    result.trackingNumber = trackingNumber;
    result.country = country;
    
    if (country == "china" || country == "cn") {
        return trackChina(trackingNumber, appType);
    } else if (country == "usa" || country == "us") {
        return trackUSA(trackingNumber, appType);
    } else if (country == "europe" || country == "eu") {
        return trackEurope(trackingNumber, appType);
    } else if (country == "japan" || country == "jp") {
        return trackJapan(trackingNumber, appType);
    }
    
    result.success = false;
    result.error = "不支持的国家: " + country;
    return result;
}

TrackingResult ProgressTracker::trackChina(const QString& trackingNumber, const QString& appType)
{
    CNIPAResult cnipaResult;
    
    if (appType == "software_copyright") {
        cnipaResult = m_cnipaTracker->trackSoftwareCopyright(trackingNumber);
    } else if (appType == "trademark") {
        cnipaResult = m_cnipaTracker->trackTrademark(trackingNumber);
    } else if (appType == "patent") {
        cnipaResult = m_cnipaTracker->trackPatent(trackingNumber);
    }
    
    TrackingResult result;
    result.success = cnipaResult.success;
    result.trackingNumber = cnipaResult.trackingNumber;
    result.country = "china";
    result.currentStatus = cnipaResult.currentStatus;
    result.statusCode = cnipaResult.statusCode;
    result.estimatedCompletion = cnipaResult.estimatedCompletion;
    result.error = cnipaResult.error;
    
    for (const auto& step : cnipaResult.steps) {
        result.steps.append({step.status, step.date, step.description});
    }
    
    emit trackingCompleted(result);
    return result;
}

TrackingResult ProgressTracker::trackUSA(const QString& trackingNumber, const QString& appType)
{
    // TODO: 实现美国 USPTO 查询
    TrackingResult result;
    result.success = true;
    result.trackingNumber = trackingNumber;
    result.country = "usa";
    result.currentStatus = "Pending";
    result.statusCode = "pending";
    result.estimatedCompletion = "2024-12-01";
    
    result.steps.append({"Filed", "2024-01-20", "Application filed with USPTO"});
    result.steps.append({"Under Examination", "2024-03-01", "Under substantive examination"});
    
    emit trackingCompleted(result);
    return result;
}

TrackingResult ProgressTracker::trackEurope(const QString& trackingNumber, const QString& appType)
{
    // TODO: 实现欧洲 EPO 查询
    TrackingResult result;
    result.success = true;
    result.trackingNumber = trackingNumber;
    result.country = "europe";
    result.currentStatus = "Examination";
    result.statusCode = "examination";
    
    result.steps.append({"Filed", "2024-01-10", "Application filed with EPO"});
    
    emit trackingCompleted(result);
    return result;
}

TrackingResult ProgressTracker::trackJapan(const QString& trackingNumber, const QString& appType)
{
    // TODO: 实现日本 JPO 查询
    TrackingResult result;
    result.success = true;
    result.trackingNumber = trackingNumber;
    result.country = "japan";
    result.currentStatus = "審査中";
    result.statusCode = "under_review";
    
    result.steps.append({"出願", "2024-01-15", "出願が受理されました"});
    
    emit trackingCompleted(result);
    return result;
}

QList<TrackingResult> ProgressTracker::batchTrack(const QList<QJsonObject>& queries)
{
    QList<TrackingResult> results;
    
    for (const auto& query : queries) {
        QString country = query["country"].toString();
        QString trackingNumber = query["tracking_number"].toString();
        QString appType = query["type"].toString();
        
        results.append(trackByCountry(country, trackingNumber, appType));
    }
    
    emit batchTrackingCompleted(results);
    return results;
}