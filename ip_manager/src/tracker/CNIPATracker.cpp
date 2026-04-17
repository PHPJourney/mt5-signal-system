#include "CNIPATracker.h"
#include "src/utils/Logger.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QEventLoop>
#include <QTimer>

CNIPATracker::CNIPATracker(QObject *parent)
    : QObject(parent), m_networkManager(new QNetworkAccessManager(this))
{
    LOG_INFO("中国知识产权局追踪器初始化完成");
}

CNIPAResult CNIPATracker::trackSoftwareCopyright(const QString& trackingNumber)
{
    return track(trackingNumber, "software_copyright");
}

CNIPAResult CNIPATracker::trackTrademark(const QString& trackingNumber)
{
    return track(trackingNumber, "trademark");
}

CNIPAResult CNIPATracker::trackPatent(const QString& trackingNumber)
{
    return track(trackingNumber, "patent");
}

CNIPAResult CNIPATracker::track(const QString& trackingNumber, const QString& type)
{
    LOG_INFO("查询中国申请进度: " + trackingNumber + " 类型: " + type);
    
    CNIPAResult result;
    result.trackingNumber = trackingNumber;
    
    // TODO: 实际调用中国知识产权局 API
    // 这里返回模拟数据
    
    result.success = true;
    result.currentStatus = "审查中";
    result.statusCode = "under_review";
    result.estimatedCompletion = "2024-06-15";
    
    // 模拟进度步骤
    result.steps.append({"已受理", "2024-01-15", "申请文件已提交，正式受理"});
    result.steps.append({"形式审查", "2024-02-01", "形式审查通过"});
    result.steps.append({"实质审查", "2024-03-10", "进入实质审查阶段"});
    
    emit trackingCompleted(result);
    return result;
}

CNIPAResult CNIPATracker::fetchFromAPI(const QString& trackingNumber, const QString& type)
{
    CNIPAResult result;
    
    // TODO: 实现实际的 HTTP 请求
    // QString url = m_apiBaseUrl + "/query/" + type + "/" + trackingNumber;
    // QNetworkRequest request(url);
    // QNetworkReply* reply = m_networkManager->get(request);
    
    // QEventLoop loop;
    // connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    // QTimer::singleShot(10000, &loop, &QEventLoop::quit);
    // loop.exec();
    
    // if (reply->error() == QNetworkReply::NoError) {
    //     QString response = reply->readAll();
    //     result = parseResponse(response);
    // }
    
    return result;
}

CNIPAResult CNIPATracker::parseResponse(const QString& response)
{
    CNIPAResult result;
    
    QJsonParseError parseError;
    QJsonDocument doc = QJsonDocument::fromJson(response.toUtf8(), &parseError);
    
    if (parseError.error != QJsonParseError::NoError) {
        result.success = false;
        result.error = "JSON 解析失败: " + parseError.errorString();
        return result;
    }
    
    QJsonObject json = doc.object();
    result.success = json["success"].toBool();
    result.trackingNumber = json["tracking_number"].toString();
    result.currentStatus = json["current_status"].toString();
    result.statusCode = json["status_code"].toString();
    result.estimatedCompletion = json["estimated_completion"].toString();
    
    // 解析步骤
    QJsonArray stepsArray = json["steps"].toArray();
    for (const QJsonValue& stepValue : stepsArray) {
        QJsonObject stepObj = stepValue.toObject();
        CNIPAStep step;
        step.status = stepObj["status"].toString();
        step.date = stepObj["date"].toString();
        step.description = stepObj["description"].toString();
        result.steps.append(step);
    }
    
    if (!result.success) {
        result.error = json["error"].toString();
    }
    
    return result;
}