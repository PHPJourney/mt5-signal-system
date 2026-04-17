// src/ai/AIGenerator.h - AI 文件生成器
#ifndef AIGENERATOR_H
#define AIGENERATOR_H

#include <QObject>
#include <QString>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QTimer>

class AIGenerator : public QObject
{
    Q_OBJECT

public:
    explicit AIGenerator(QObject *parent = nullptr);
    ~AIGenerator();
    
    // 配置
    void setAPIKey(const QString& apiKey);
    void setProvider(const QString& provider);  // openai / aliyun / baidu
    void setModel(const QString& model);
    
    // 生成软件著作权申请文件
    void generateSoftwareCopyrightDoc(
        const QString& name,
        const QString& version,
        const QString& language,
        int linesOfCode,
        const QString& description,
        const QStringList& features,
        const QString& hardwareEnv,
        const QString& softwareEnv
    );
    
    // 生成商标申请文件
    void generateTrademarkDoc(
        const QString& name,
        int category,
        const QString& applicant,
        const QString& address,
        const QString& description,
        const QString& logoDescription
    );
    
    // 生成专利申请文件
    void generatePatentDoc(
        const QString& title,
        const QString& type,
        const QString& inventor,
        const QString& applicant,
        const QString& abstract,
        const QString& background,
        const QString& inventionContent,
        const QString& claims,
        const QString& drawings
    );
    
    // 分析代码并生成说明文档
    void generateCodeDescription(
        const QString& code,
        const QString& language = "cpp"
    );
    
    // 保存文档到文件
    bool saveDocument(const QString& content, const QString& type, const QString& outputPath = QString());

signals:
    void generationCompleted(const QString& document, const QString& type);
    void generationError(const QString& error);
    void generationProgress(int percent);

private slots:
    void onReplyFinished(QNetworkReply* reply);
    void onRequestTimeout();

private:
    QString buildPrompt(const QString& type, const QStringList& args);
    void callAI(const QString& prompt, const QString& type);
    QString parseAIResponse(const QString& response);
    
    QString m_apiKey;
    QString m_provider = "openai";
    QString m_model = "gpt-4";
    QString m_currentType;
    
    QNetworkAccessManager* m_networkManager;
    QTimer* m_timeoutTimer;
    
    QMap<QString, QString> m_endpoints;
    QMap<QString, QString> m_models;
};

#endif // AIGENERATOR_H
