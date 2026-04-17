#ifndef CNIPATRACKER_H
#define CNIPATRACKER_H

#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QList>
#include <QNetworkAccessManager>
#include <QNetworkReply>

struct CNIPAStep {
    QString status;
    QString date;
    QString description;
};

struct CNIPAResult {
    bool success;
    QString trackingNumber;
    QString currentStatus;
    QString statusCode;
    QList<CNIPAStep> steps;
    QString estimatedCompletion;
    QString error;
};

class CNIPATracker : public QObject
{
    Q_OBJECT

public:
    explicit CNIPATracker(QObject *parent = nullptr);
    
    // 查询软件著作权进度
    CNIPAResult trackSoftwareCopyright(const QString& trackingNumber);
    
    // 查询商标注册进度
    CNIPAResult trackTrademark(const QString& trackingNumber);
    
    // 查询专利进度
    CNIPAResult trackPatent(const QString& trackingNumber);
    
    // 通用查询接口
    CNIPAResult track(const QString& trackingNumber, const QString& type);

signals:
    void trackingCompleted(const CNIPAResult& result);
    void trackingError(const QString& error);

private:
    CNIPAResult fetchFromAPI(const QString& trackingNumber, const QString& type);
    CNIPAResult parseResponse(const QString& response);
    
    QNetworkAccessManager* m_networkManager;
    QString m_apiBaseUrl = "https://api.cnipa.gov.cn/v1";
};

#endif // CNIPATRACKER_H