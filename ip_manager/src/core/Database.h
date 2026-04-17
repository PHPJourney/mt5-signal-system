#ifndef DATABASE_H
#define DATABASE_H

#include <QObject>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QSqlError>
#include <QString>
#include <QList>
#include <QVariantMap>

class Database : public QObject
{
    Q_OBJECT

public:
    static bool init();
    static void close();
    static bool isOpen();
    
    // 申请记录 CRUD
    static int addApplication(const QVariantMap& data);
    static bool updateApplication(int id, const QVariantMap& data);
    static QVariantMap getApplication(int id);
    static QList<QVariantMap> getAllApplications(const QString& type = "", const QString& status = "");
    static bool deleteApplication(int id);
    
    // 支付记录
    static int addPayment(int appId, double amount, const QString& method, const QString& paymentId = "");
    static QList<QVariantMap> getPayments(int appId);
    static bool updatePaymentStatus(int id, const QString& status);
    
    // 进度跟踪
    static int addTrackingLog(int appId, const QString& status, const QString& description = "");
    static QList<QVariantMap> getTrackingLogs(int appId);
    
    // 文件记录
    static int addFile(int appId, const QString& fileType, const QString& filePath, 
                       const QString& fileName = "", int fileSize = 0);
    static QList<QVariantMap> getFiles(int appId);
    
    // 统计
    static int getApplicationCount(const QString& type = "");
    static int getPaymentCount(const QString& status = "");

private:
    static QSqlDatabase db;
    static bool createTables();
    static bool createApplicationsTable();
    static bool createPaymentsTable();
    static bool createTrackingLogsTable();
    static bool createFilesTable();
};

#endif // DATABASE_H