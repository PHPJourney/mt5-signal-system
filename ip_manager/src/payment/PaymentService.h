// src/payment/PaymentService.h - 支付服务
#ifndef PAYMENTSERVICE_H
#define PAYMENTSERVICE_H

#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>

class PaymentService : public QObject
{
    Q_OBJECT

public:
    explicit PaymentService(QObject *parent = nullptr);
    ~PaymentService();
    
    // 配置
    void setAlipayConfig(const QString& appId, const QString& notifyUrl, const QString& returnUrl);
    void setWechatConfig(const QString& appId, const QString& mchId, const QString& apiKey);
    
    // 创建支付订单
    QJsonObject createAlipayOrder(int appId, double amount, const QString& subject,
                                  const QString& notifyUrl = QString(), const QString& returnUrl = QString());
    QJsonObject createWechatOrder(int appId, double amount, const QString& description,
                                  const QString& notifyUrl = QString());
    QJsonObject createBankTransferOrder(int appId, double amount, const QString& recipient);
    
    // 验证支付
    bool verifyAlipayPayment(const QString& orderNo);
    bool verifyWechatPayment(const QString& orderNo);
    
    // 生成订单号
    static QString generateOrderNo();

signals:
    void paymentCreated(const QString& orderNo, const QString& paymentUrl, const QString& method);
    void paymentVerified(bool success, const QString& orderNo);
    void paymentError(const QString& error);

private:
    QString signAlipay(const QJsonObject& params);
    QString buildAlipayUrl(const QString& gatewayUrl, const QJsonObject& params);
    QString generateWechatSign(const QJsonObject& params);
    
    // 支付宝配置
    QString m_alipayAppId;
    QString m_alipayNotifyUrl;
    QString m_alipayReturnUrl;
    
    // 微信支付配置
    QString m_wechatAppId;
    QString m_wechatMchId;
    QString m_wechatApiKey;
    
    QNetworkAccessManager* m_networkManager;
};

#endif // PAYMENTSERVICE_H
