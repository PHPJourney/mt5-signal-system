#include "AIGenerator.h"
#include "src/utils/Logger.h"
#include <QFile>
#include <QDir>
#include <QStandardPaths>
#include <QDateTime>
#include <QRegularExpression>

AIGenerator::AIGenerator(QObject *parent)
    : QObject(parent), m_networkManager(new QNetworkAccessManager(this)),
      m_timeoutTimer(new QTimer(this))
{
    // API 端点配置
    m_endpoints["openai"] = "https://api.openai.com/v1/chat/completions";
    m_endpoints["aliyun"] = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation";
    m_endpoints["baidu"] = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions";
    
    // 模型配置
    m_models["openai"] = "gpt-4";
    m_models["aliyun"] = "qwen-max";
    m_models["baidu"] = "ernie-bot-4";
    
    m_timeoutTimer->setSingleShot(true);
    m_timeoutTimer->setInterval(60000); // 60秒超时
    
    connect(m_timeoutTimer, &QTimer::timeout, this, &AIGenerator::onRequestTimeout);
    
    LOG_INFO("AI 生成器初始化完成");
}

AIGenerator::~AIGenerator()
{
    LOG_INFO("AI 生成器销毁");
}

void AIGenerator::setAPIKey(const QString& apiKey)
{
    m_apiKey = apiKey;
}

void AIGenerator::setProvider(const QString& provider)
{
    m_provider = provider;
}

void AIGenerator::setModel(const QString& model)
{
    m_model = model;
}

void AIGenerator::generateSoftwareCopyrightDoc(const QString& name, const QString& version,
                                                const QString& language, int linesOfCode,
                                                const QString& description, const QStringList& features,
                                                const QString& hardwareEnv, const QString& softwareEnv)
{
    QStringList args = {name, version, language, QString::number(linesOfCode), 
                       description, features.join(", "), hardwareEnv, softwareEnv};
    QString prompt = buildPrompt("software_copyright", args);
    callAI(prompt, "software_copyright");
}

void AIGenerator::generateTrademarkDoc(const QString& name, int category,
                                        const QString& applicant, const QString& address,
                                        const QString& description, const QString& logoDescription)
{
    QStringList args = {name, QString::number(category), applicant, address, description, logoDescription};
    QString prompt = buildPrompt("trademark", args);
    callAI(prompt, "trademark");
}

void AIGenerator::generatePatentDoc(const QString& title, const QString& type,
                                     const QString& inventor, const QString& applicant,
                                     const QString& abstract, const QString& background,
                                     const QString& inventionContent, const QString& claims,
                                     const QString& drawings)
{
    QStringList args = {title, type, inventor, applicant, abstract, background, 
                       inventionContent, claims, drawings};
    QString prompt = buildPrompt("patent", args);
    callAI(prompt, "patent");
}

void AIGenerator::generateCodeDescription(const QString& code, const QString& language)
{
    QString prompt = QString("请分析以下 %1 代码，并生成软件著作权申请所需的代码说明文档：\n\n"
                            "```\n%2\n```\n\n"
                            "请生成：\n"
                            "1. 代码功能说明\n"
                            "2. 主要模块和类说明\n"
                            "3. 核心算法说明\n"
                            "4. 代码结构说明\n"
                            "5. 技术特点\n\n"
                            "使用正式的技术文档格式。").arg(language, code.left(3000));
    
    callAI(prompt, "code_description");
}

QString AIGenerator::buildPrompt(const QString& type, const QStringList& args)
{
    if (type == "software_copyright") {
        return QString("请生成一份软件著作权申请文件，包含以下内容：\n\n"
                      "软件名称：%1\n"
                      "版本号：%2\n"
                      "编程语言：%3\n"
                      "代码行数：约 %4 行\n"
                      "软件描述：%5\n"
                      "功能特点：%6\n"
                      "硬件环境：%7\n"
                      "软件环境：%8\n\n"
                      "请按照中国软件著作权申请标准格式生成，包含：\n"
                      "1. 软件名称和版本号\n"
                      "2. 软件开发目的\n"
                      "3. 主要功能和特点\n"
                      "4. 技术特点\n"
                      "5. 运行环境\n"
                      "6. 开发完成日期\n\n"
                      "使用正式的法律文书格式。")
               .arg(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7]);
    } else if (type == "trademark") {
        return QString("请生成一份商标注册申请文件：\n\n"
                      "商标名称：%1\n"
                      "商标类别：第 %2 类\n"
                      "申请人：%3\n"
                      "地址：%4\n"
                      "商标描述：%5\n"
                      "图样描述：%6\n\n"
                      "请按照商标注册申请标准格式生成，包含：\n"
                      "1. 申请人信息\n"
                      "2. 商标图样说明\n"
                      "3. 指定商品/服务项目\n"
                      "4. 商标使用声明\n"
                      "5. 申请日期\n\n"
                      "使用正式的法律文书格式。")
               .arg(args[0], args[1], args[2], args[3], args[4], args[5]);
    } else if (type == "patent") {
        return QString("请生成一份专利申请文件：\n\n"
                      "专利名称：%1\n"
                      "专利类型：%2\n"
                      "发明人：%3\n"
                      "申请人：%4\n"
                      "摘要：%5\n"
                      "背景技术：%6\n"
                      "发明内容：%7\n"
                      "权利要求要点：%8\n"
                      "附图说明：%9\n\n"
                      "请按照专利申请标准格式生成，包含：\n"
                      "1. 技术领域\n"
                      "2. 背景技术\n"
                      "3. 发明内容\n"
                      "4. 附图说明\n"
                      "5. 具体实施方式\n"
                      "6. 权利要求书\n\n"
                      "使用正式的专利文书格式。")
               .arg(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8]);
    }
    
    return "";
}

void AIGenerator::callAI(const QString& prompt, const QString& type)
{
    if (m_apiKey.isEmpty()) {
        emit generationError("API Key 未设置，请在设置中配置");
        return;
    }
    
    m_currentType = type;
    emit generationProgress(10);
    
    QString endpoint = m_endpoints.value(m_provider, m_endpoints["openai"]);
    QString modelName = m_model.isEmpty() ? m_models.value(m_provider) : m_model;
    
    QJsonObject requestBody;
    QJsonArray messages;
    
    messages.append(QJsonObject{
        {"role", "system"},
        {"content", "你是一个专业的知识产权申请文件生成助手，擅长生成符合各国知识产权局要求的申请文件。"}
    });
    messages.append(QJsonObject{
        {"role", "user"},
        {"content", prompt}
    });
    
    if (m_provider == "openai") {
        requestBody["model"] = modelName;
        requestBody["messages"] = messages;
        requestBody["max_tokens"] = 4000;
        requestBody["temperature"] = 0.7;
    } else if (m_provider == "aliyun") {
        requestBody["model"] = modelName;
        requestBody["input"] = QJsonObject{{"messages", messages}};
        requestBody["parameters"] = QJsonObject{{"max_tokens", 4000}, {"temperature", 0.7}};
    }
    
    QJsonDocument doc(requestBody);
    QByteArray jsonData = doc.toJson();
    
    QNetworkRequest request(QUrl(endpoint));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setRawHeader("Authorization", QString("Bearer %1").arg(m_apiKey).toUtf8());
    
    LOG_INFO("调用 AI API: " + m_provider + " - " + modelName);
    
    emit generationProgress(30);
    
    QNetworkReply* reply = m_networkManager->post(request, jsonData);
    
    connect(reply, &QNetworkReply::finished, this, &AIGenerator::onReplyFinished);
    
    m_timeoutTimer->start();
    emit generationProgress(50);
}

void AIGenerator::onReplyFinished(QNetworkReply* reply)
{
    m_timeoutTimer->stop();
    
    emit generationProgress(80);
    
    if (reply->error() != QNetworkReply::NoError) {
        QString error = QString("AI API 请求失败: %1").arg(reply->errorString());
        LOG_ERROR(error);
        emit generationError(error);
        reply->deleteLater();
        return;
    }
    
    QString response = reply->readAll();
    LOG_DEBUG("AI API 响应: " + response.left(200));
    
    QString result = parseAIResponse(response);
    
    if (!result.isEmpty()) {
        LOG_INFO("AI 文档生成成功: " + m_currentType);
        emit generationProgress(100);
        emit generationCompleted(result, m_currentType);
    } else {
        emit generationError("AI 响应解析失败");
    }
    
    reply->deleteLater();
}

QString AIGenerator::parseAIResponse(const QString& response)
{
    QJsonParseError parseError;
    QJsonDocument doc = QJsonDocument::fromJson(response.toUtf8(), &parseError);
    
    if (parseError.error != QJsonParseError::NoError) {
        LOG_ERROR("JSON 解析失败: " + parseError.errorString());
        return "";
    }
    
    QJsonObject json = doc.object();
    
    if (m_provider == "openai") {
        QJsonArray choices = json["choices"].toArray();
        if (!choices.isEmpty()) {
            QJsonObject firstChoice = choices[0].toObject();
            QJsonObject message = firstChoice["message"].toObject();
            return message["content"].toString();
        }
    } else if (m_provider == "aliyun") {
        QJsonObject output = json["output"].toObject();
        return output["text"].toString();
    }
    
    return "";
}

void AIGenerator::onRequestTimeout()
{
    LOG_ERROR("AI API 请求超时");
    emit generationError("请求超时，请检查网络连接或 API 配置");
}

bool AIGenerator::saveDocument(const QString& content, const QString& type, const QString& outputPath)
{
    QString dir = outputPath;
    if (dir.isEmpty()) {
        dir = QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation) + "/IPManager";
    }
    
    QDir().mkpath(dir);
    
    QString timestamp = QDateTime::currentDateTime().toString("yyyyMMdd_HHmmss");
    QString filename = QString("%1_%2.md").arg(type, timestamp);
    QString filepath = dir + "/" + filename;
    
    QFile file(filepath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        LOG_ERROR("无法创建文件: " + filepath);
        return false;
    }
    
    QTextStream out(&file);
    out.setEncoding(QStringConverter::Utf8);
    out << "# " << type << " 申请文件\n\n";
    out << "生成时间: " << QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss") << "\n\n";
    out << "---\n\n";
    out << content;
    
    file.close();
    
    LOG_INFO("文档已保存: " + filepath);
    return true;
}