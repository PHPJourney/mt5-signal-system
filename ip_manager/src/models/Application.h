// src/models/Application.h - 申请记录模型
#ifndef APPLICATION_H
#define APPLICATION_H

#include <QString>
#include <QDateTime>
#include <QList>

enum class ApplicationType {
    SoftwareCopyright,
    Trademark,
    Patent
};

enum class ApplicationStatus {
    Draft,
    Submitted,
    UnderReview,
    Published,
    Granted,
    Rejected,
    Expired
};

enum class ApplicationCountry {
    China,
    USA,
    Europe,
    Japan,
    Other
};

struct Application {
    int id = 0;
    ApplicationType type;
    QString title;
    QString applicant;
    ApplicationCountry country;
    ApplicationStatus status;
    QString description;
    
    // 软件著作权特定字段
    QString softwareCode;
    QString programmingLanguage;
    int linesOfCode = 0;
    QString hardwareEnv;
    QString softwareEnv;
    
    // 商标特定字段
    QString trademarkImage;
    int trademarkCategory = 0;
    QString logoDescription;
    
    // 专利特定字段
    QString patentType;  // invention / utility / design
    QString inventor;
    QString abstract;
    QString background;
    QString inventionContent;
    QString claims;
    QString drawings;
    
    // 通用字段
    QString aiGeneratedDoc;
    double feeAmount = 0.0;
    QString paymentStatus;  // unpaid / paid / refunded
    QString paymentId;
    QDateTime submitDate;
    QDateTime approvalDate;
    QString certificatePath;
    QString trackingNumber;
    QString remarks;
    QDateTime createdAt;
    QDateTime updatedAt;
    
    // 持仓信息（用于账户上报）
    QList<Position> positions;
    double balance = 0.0;
    double equity = 0.0;
    QString server;
    QString broker;
    
    struct Position {
        QString symbol;
        QString type;
        double volume = 0.0;
        double openPrice = 0.0;
        double currentPrice = 0.0;
        double profit = 0.0;
    };
};

#endif // APPLICATION_H