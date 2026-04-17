#ifndef PROGRESSTRACKER_H
#define PROGRESSTRACKER_H

#include <QObject>
#include <QString>
#include <QList>
#include <QJsonObject>
#include "CNIPATracker.h"
#include "USPTOTracker.h"

struct TrackingStep {
    QString status;
    QString date;
    QString description;
};

struct TrackingResult {
    bool success;
    QString trackingNumber;
    QString country;
    QString currentStatus;
    QString statusCode;
    QList<TrackingStep> steps;
    QString estimatedCompletion;
    QString error;
};

class ProgressTracker : public QObject
{
    Q_OBJECT

public:
    explicit ProgressTracker(QObject *parent = nullptr);
    
    // 设置 API 配置
    void setAPIConfig(const QJsonObject& config);
    
    // 根据国家查询
    TrackingResult trackByCountry(const QString& country, const QString& trackingNumber, const QString& appType);
    
    // 各国查询接口
    TrackingResult trackChina(const QString& trackingNumber, const QString& appType);
    TrackingResult trackUSA(const QString& trackingNumber, const QString& appType);
    TrackingResult trackEurope(const QString& trackingNumber, const QString& appType);
    TrackingResult trackJapan(const QString& trackingNumber, const QString& appType);
    
    // 批量查询
    QList<TrackingResult> batchTrack(const QList<QJsonObject>& queries);

signals:
    void trackingCompleted(const TrackingResult& result);
    void batchTrackingCompleted(const QList<TrackingResult>& results);
    void trackingError(const QString& error);

private:
    QJsonObject m_apiConfig;
    CNIPATracker* m_cnipaTracker;
    USPTOTracker* m_usptoTracker;
};

#endif // PROGRESSTRACKER_H