#include "PaymentService.h"
#include "src/utils/Logger.h"
#include <QDateTime>
#include <QUuid>
#include <QCryptographicHash>
#include <QUrlQuery>
#include <QJsonDocument>

PaymentService::PaymentService(QObject *parent)
    : QObject(parent), m_networkManager(new QNetworkAccessManager(this))
{
    LOG_INFO("支付服务初始化完成");
}

PaymentService::~PaymentService()
{
    LOG_INFO("支付服务销毁");
}

void PaymentService::setAlipayConfig(const QString& appId, const QString& notifyUrl, const QString& returnUrl)
{
    m_alipayAppId = appId;
    m_alipayNotifyUrl = notifyUrl;
    m_alipayReturnUrl = returnUrl;
}

void PaymentService::setWechatConfig(const QString& appId, const QString& mchId, const QString& apiKey)
{
    m_wechatAppId = appId;
    m_wechatMchId = mchId;
    m_wechatApiKey = apiKey;
}

QJsonObject PaymentService::createAlipayOrder(int appId, double amount, const QString& subject,
                                               const QString& notifyUrl, const QString& returnUrl)
{
    QString orderNo = generateOrderNo();
    
    QJsonObject result;
    result["order_no"] = orderNo;
    result["amount"] = amount;
    result["method"] = "alipay";
    
    // 构建支付宝请求参数
    QJsonObject bizContent;
    bizContent["out_trade_no"] = orderNo;
    bizContent["total_amount"] = QString::number(amount, 'f', 2);
    bizContent["subject"] = subject;
    bizContent["product_code"] = "FAST_INSTANT_TRADE_PAY";
    bizContent["notify_url"] = notifyUrl.isEmpty() ? m_alipayNotifyUrl : notifyUrl;
    bizContent["return_url"] = returnUrl.isEmpty() ? m_alipayReturnUrl : returnUrl;
    
    QJsonObject params;
    params["app_id"] = m_alipayAppId;
    params["method"] = "alipay.trade.page.pay";
    params["charset"] = "utf-8";
    params["sign_type"] = "RSA2";
    params["timestamp"] = QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss");
    params["version"] = "1.0";
    params["biz_content"] = QJsonDocument(bizContent).toJson(QJsonDocument::Compact);
    
    // 签名
    params["sign"] = signAlipay(params);
    
    // 构建支付链接
    QString gatewayUrl = "https://openapi.alipay.com/gateway.do";
    QString payUrl = buildAlipayUrl(gatewayUrl, params);
    
    result["payment_url"] = payUrl;
    
    LOG_INFO("支付宝订单创建成功: " + orderNo + " 金额: " + QString::number(amount));
    emit paymentCreated(orderNo, payUrl, "alipay");
    
    return result;
}

QJsonObject PaymentService::createWechatOrder(int appId, double amount, const QString& description,
                                               const QString& notifyUrl)
{
    QString orderNo = generateOrderNo();
    
    QJsonObject result;
    result["order_no"] = orderNo;
    result["amount"] = amount;
    result["method"] = "wechat";
    
    // 构建微信支付请求
    QJsonObject requestBody;
    requestBody["appid"] = m_wechatAppId;
    requestBody["mchid"] = m_wechatMchId;
    requestBody["description"] = description;
    requestBody["out_trade_no"] = orderNo;
    requestBody["notify_url"] = notifyUrl.isEmpty() ? "https://your-domain.com/api/payment/wechat/notify" : notifyUrl;
    
    QJsonObject amountObj;
    amountObj["total"] = static_cast<int>(amount * 100); // 转换为分
    amountObj["currency"] = "CNY";
    requestBody["amount"] = amountObj;
    
    // TODO: 实际调用微信支付 API
    // 这里返回模拟数据
    QString codeUrl = QString("weixin://wxpay/bizpayurl?pr=%1").arg(orderNo);
    result["payment_url"] = codeUrl;
    result["code_url"] = codeUrl;
    
    LOG_INFO("微信订单创建成功: " + orderNo + " 金额: " + QString::number(amount));
    emit paymentCreated(orderNo, codeUrl, "wechat");
    
    return result;
}

QJsonObject PaymentService::createBankTransferOrder(int appId, double amount, const QString& recipient)
{
    QString orderNo = generateOrderNo();
    
    QJsonObject result;
    result["order_no"] = orderNo;
    result["amount"] = amount;
    result["method"] = "bank_transfer";
    
    QJsonObject bankInfo;
    bankInfo["account_name"] = recipient;
    bankInfo["account_number"] = "6222 0000 0000 0000";
    bankInfo["bank_name"] = "中国银行";
    bankInfo["remark"] = QString("知识产权申请费用-订单%1").arg(orderNo);
    
    result["bank_info"] = bankInfo;
    
    LOG_INFO("银行转账订单创建成功: " + orderNo);
    emit paymentCreated(orderNo, "", "bank_transfer");
    
    return result;
}

bool PaymentService::verifyAlipayPayment(const QString& orderNo)
{
    // TODO: 实际调用支付宝查询 API
    LOG_INFO("验证支付宝支付: " + orderNo);
    emit paymentVerified(true, orderNo);
    return true;
}

bool PaymentService::verifyWechatPayment(const QString& orderNo)
{
    // TODO: 实际调用微信支付查询 API
    LOG_INFO("验证微信支付: " + orderNo);
    emit paymentVerified(true, orderNo);
    return true;
}

QString PaymentService::generateOrderNo()
{
    QString timestamp = QDateTime::currentDateTime().toString("yyyyMMddHHmmss");
    QString randomStr = QUuid::createUuid().toString().mid(1, 8);
    return QString("IP%1%2").arg(timestamp, randomStr);
}

QString PaymentService::signAlipay(const QJsonObject& params)
{
    // TODO: 实际实现 RSA2 签名算法
    // 这里返回模拟签名
    return "mock_rsa2_signature";
}

QString PaymentService::buildAlipayUrl(const QString& gatewayUrl, const QJsonObject& params)
{
    QUrlQuery query;
    for (auto it = params.constBegin(); it != params.constEnd(); ++it) {
        query.addQueryItem(it.key(), it.value().toString());
    }
    
    QUrl url(gatewayUrl);
    url.setQuery(query);
    return url.toString();
}

QString PaymentService::generateWechatSign(const QJsonObject& params)
{
    // TODO: 实际实现微信支付签名算法
    return "mock_wechat_sign";
}