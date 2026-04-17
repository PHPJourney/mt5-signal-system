#include "Database.h"
#include "src/utils/Logger.h"
#include <QFile>
#include <QDir>
#include <QStandardPaths>
#include <QDateTime>

QSqlDatabase Database::db;

bool Database::init()
{
    LOG_INFO("初始化数据库");
    
    QString dbPath = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) 
                     + "/ip_manager.db";
    QDir().mkpath(QFileInfo(dbPath).absolutePath());
    
    LOG_INFO("数据库路径: " + dbPath);
    
    db = QSqlDatabase::addDatabase("QSQLITE");
    db.setDatabaseName(dbPath);
    
    if (!db.open()) {
        LOG_ERROR("无法打开数据库: " + db.lastError().text());
        return false;
    }
    
    if (!createTables()) {
        LOG_ERROR("创建数据表失败");
        return false;
    }
    
    LOG_INFO("数据库初始化成功");
    return true;
}

void Database::close()
{
    if (db.isOpen()) {
        db.close();
        LOG_INFO("数据库已关闭");
    }
}

bool Database::isOpen()
{
    return db.isOpen();
}

bool Database::createTables()
{
    return createApplicationsTable() && 
           createPaymentsTable() && 
           createTrackingLogsTable() && 
           createFilesTable();
}

bool Database::createApplicationsTable()
{
    QString sql = R"(
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            applicant TEXT NOT NULL,
            country TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            description TEXT,
            
            software_code TEXT,
            programming_language TEXT,
            lines_of_code INTEGER DEFAULT 0,
            hardware_env TEXT,
            software_env TEXT,
            
            trademark_image TEXT,
            trademark_category INTEGER DEFAULT 0,
            logo_description TEXT,
            
            patent_type TEXT,
            inventor TEXT,
            abstract TEXT,
            background TEXT,
            invention_content TEXT,
            claims TEXT,
            drawings TEXT,
            
            ai_generated_doc TEXT,
            fee_amount REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'unpaid',
            payment_id TEXT,
            submit_date TEXT,
            approval_date TEXT,
            certificate_path TEXT,
            tracking_number TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    )";
    
    QSqlQuery query;
    if (!query.exec(sql)) {
        LOG_ERROR("创建 applications 表失败: " + query.lastError().text());
        return false;
    }
    
    return true;
}

bool Database::createPaymentsTable()
{
    QString sql = R"(
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            payment_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    )";
    
    QSqlQuery query;
    if (!query.exec(sql)) {
        LOG_ERROR("创建 payments 表失败: " + query.lastError().text());
        return false;
    }
    
    return true;
}

bool Database::createTrackingLogsTable()
{
    QString sql = R"(
        CREATE TABLE IF NOT EXISTS tracking_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    )";
    
    QSqlQuery query;
    if (!query.exec(sql)) {
        LOG_ERROR("创建 tracking_logs 表失败: " + query.lastError().text());
        return false;
    }
    
    return true;
}

bool Database::createFilesTable()
{
    QString sql = R"(
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT,
            file_size INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    )";
    
    QSqlQuery query;
    if (!query.exec(sql)) {
        LOG_ERROR("创建 files 表失败: " + query.lastError().text());
        return false;
    }
    
    return true;
}

int Database::addApplication(const QVariantMap& data)
{
    QSqlQuery query;
    query.prepare(R"(
        INSERT INTO applications (
            type, title, applicant, country, status, description,
            software_code, programming_language, lines_of_code,
            hardware_env, software_env,
            trademark_image, trademark_category, logo_description,
            patent_type, inventor, abstract, background,
            invention_content, claims, drawings,
            ai_generated_doc, fee_amount, payment_status,
            payment_id, tracking_number, remarks
        ) VALUES (
            :type, :title, :applicant, :country, :status, :description,
            :software_code, :programming_language, :lines_of_code,
            :hardware_env, :software_env,
            :trademark_image, :trademark_category, :logo_description,
            :patent_type, :inventor, :abstract, :background,
            :invention_content, :claims, :drawings,
            :ai_generated_doc, :fee_amount, :payment_status,
            :payment_id, :tracking_number, :remarks
        )
    )");
    
    query.bindValue(":type", data.value("type"));
    query.bindValue(":title", data.value("title"));
    query.bindValue(":applicant", data.value("applicant"));
    query.bindValue(":country", data.value("country"));
    query.bindValue(":status", data.value("status", "draft"));
    query.bindValue(":description", data.value("description", ""));
    query.bindValue(":software_code", data.value("software_code", ""));
    query.bindValue(":programming_language", data.value("programming_language", ""));
    query.bindValue(":lines_of_code", data.value("lines_of_code", 0));
    query.bindValue(":hardware_env", data.value("hardware_env", ""));
    query.bindValue(":software_env", data.value("software_env", ""));
    query.bindValue(":trademark_image", data.value("trademark_image", ""));
    query.bindValue(":trademark_category", data.value("trademark_category", 0));
    query.bindValue(":logo_description", data.value("logo_description", ""));
    query.bindValue(":patent_type", data.value("patent_type", ""));
    query.bindValue(":inventor", data.value("inventor", ""));
    query.bindValue(":abstract", data.value("abstract", ""));
    query.bindValue(":background", data.value("background", ""));
    query.bindValue(":invention_content", data.value("invention_content", ""));
    query.bindValue(":claims", data.value("claims", ""));
    query.bindValue(":drawings", data.value("drawings", ""));
    query.bindValue(":ai_generated_doc", data.value("ai_generated_doc", ""));
    query.bindValue(":fee_amount", data.value("fee_amount", 0.0));
    query.bindValue(":payment_status", data.value("payment_status", "unpaid"));
    query.bindValue(":payment_id", data.value("payment_id", ""));
    query.bindValue(":tracking_number", data.value("tracking_number", ""));
    query.bindValue(":remarks", data.value("remarks", ""));
    
    if (query.exec()) {
        return query.lastInsertId().toInt();
    } else {
        LOG_ERROR("添加申请记录失败: " + query.lastError().text());
        return -1;
    }
}

bool Database::updateApplication(int id, const QVariantMap& data)
{
    QStringList fields;
    QStringList values;
    
    for (auto it = data.constBegin(); it != data.constEnd(); ++it) {
        fields.append(it.key() + " = ?");
        values.append(it.value());
    }
    values.append(id);
    
    QString sql = QString("UPDATE applications SET %1, updated_at = CURRENT_TIMESTAMP WHERE id = ?")
                  .arg(fields.join(", "));
    
    QSqlQuery query;
    query.prepare(sql);
    for (int i = 0; i < values.size(); ++i) {
        query.bindValue(i, values[i]);
    }
    
    if (!query.exec()) {
        LOG_ERROR("更新申请记录失败: " + query.lastError().text());
        return false;
    }
    
    return true;
}

QVariantMap Database::getApplication(int id)
{
    QSqlQuery query;
    query.prepare("SELECT * FROM applications WHERE id = ?");
    query.bindValue(0, id);
    
    if (query.exec() && query.next()) {
        QVariantMap result;
        QSqlRecord record = query.record();
        for (int i = 0; i < record.count(); ++i) {
            result[record.fieldName(i)] = record.value(i);
        }
        return result;
    }
    
    return QVariantMap();
}

QList<QVariantMap> Database::getAllApplications(const QString& type, const QString& status)
{
    QString sql = "SELECT * FROM applications WHERE 1=1";
    if (!type.isEmpty()) sql += " AND type = ?";
    if (!status.isEmpty()) sql += " AND status = ?";
    sql += " ORDER BY created_at DESC";
    
    QSqlQuery query;
    query.prepare(sql);
    
    int paramIndex = 0;
    if (!type.isEmpty()) query.bindValue(paramIndex++, type);
    if (!status.isEmpty()) query.bindValue(paramIndex++, status);
    
    QList<QVariantMap> results;
    if (query.exec()) {
        while (query.next()) {
            QVariantMap row;
            QSqlRecord record = query.record();
            for (int i = 0; i < record.count(); ++i) {
                row[record.fieldName(i)] = record.value(i);
            }
            results.append(row);
        }
    }
    
    return results;
}

bool Database::deleteApplication(int id)
{
    QSqlQuery query;
    query.prepare("DELETE FROM applications WHERE id = ?");
    query.bindValue(0, id);
    
    if (!query.exec()) {
        LOG_ERROR("删除申请记录失败: " + query.lastError().text());
        return false;
    }
    
    return true;
}

int Database::addPayment(int appId, double amount, const QString& method, const QString& paymentId)
{
    QSqlQuery query;
    query.prepare(R"(
        INSERT INTO payments (application_id, amount, payment_method, payment_id, status)
        VALUES (?, ?, ?, ?, 'pending')
    )");
    query.bindValue(0, appId);
    query.bindValue(1, amount);
    query.bindValue(2, method);
    query.bindValue(3, paymentId);
    
    if (query.exec()) {
        return query.lastInsertId().toInt();
    } else {
        LOG_ERROR("添加支付记录失败: " + query.lastError().text());
        return -1;
    }
}

QList<QVariantMap> Database::getPayments(int appId)
{
    QSqlQuery query;
    query.prepare("SELECT * FROM payments WHERE application_id = ? ORDER BY created_at DESC");
    query.bindValue(0, appId);
    
    QList<QVariantMap> results;
    if (query.exec()) {
        while (query.next()) {
            QVariantMap row;
            QSqlRecord record = query.record();
            for (int i = 0; i < record.count(); ++i) {
                row[record.fieldName(i)] = record.value(i);
            }
            results.append(row);
        }
    }
    
    return results;
}

bool Database::updatePaymentStatus(int id, const QString& status)
{
    QSqlQuery query;
    query.prepare("UPDATE payments SET status = ? WHERE id = ?");
    query.bindValue(0, status);
    query.bindValue(1, id);
    
    return query.exec();
}

int Database::addTrackingLog(int appId, const QString& status, const QString& description)
{
    QSqlQuery query;
    query.prepare("INSERT INTO tracking_logs (application_id, status, description) VALUES (?, ?, ?)");
    query.bindValue(0, appId);
    query.bindValue(1, status);
    query.bindValue(2, description);
    
    if (query.exec()) {
        return query.lastInsertId().toInt();
    }
    return -1;
}

QList<QVariantMap> Database::getTrackingLogs(int appId)
{
    QSqlQuery query;
    query.prepare("SELECT * FROM tracking_logs WHERE application_id = ? ORDER BY created_at ASC");
    query.bindValue(0, appId);
    
    QList<QVariantMap> results;
    if (query.exec()) {
        while (query.next()) {
            QVariantMap row;
            QSqlRecord record = query.record();
            for (int i = 0; i < record.count(); ++i) {
                row[record.fieldName(i)] = record.value(i);
            }
            results.append(row);
        }
    }
    
    return results;
}

int Database::addFile(int appId, const QString& fileType, const QString& filePath, 
                      const QString& fileName, int fileSize)
{
    QSqlQuery query;
    query.prepare("INSERT INTO files (application_id, file_type, file_path, file_name, file_size) VALUES (?, ?, ?, ?, ?)");
    query.bindValue(0, appId);
    query.bindValue(1, fileType);
    query.bindValue(2, filePath);
    query.bindValue(3, fileName);
    query.bindValue(4, fileSize);
    
    if (query.exec()) {
        return query.lastInsertId().toInt();
    }
    return -1;
}

QList<QVariantMap> Database::getFiles(int appId)
{
    QSqlQuery query;
    query.prepare("SELECT * FROM files WHERE application_id = ? ORDER BY created_at DESC");
    query.bindValue(0, appId);
    
    QList<QVariantMap> results;
    if (query.exec()) {
        while (query.next()) {
            QVariantMap row;
            QSqlRecord record = query.record();
            for (int i = 0; i < record.count(); ++i) {
                row[record.fieldName(i)] = record.value(i);
            }
            results.append(row);
        }
    }
    
    return results;
}

int Database::getApplicationCount(const QString& type)
{
    QSqlQuery query;
    if (!type.isEmpty()) {
        query.prepare("SELECT COUNT(*) FROM applications WHERE type = ?");
        query.bindValue(0, type);
    } else {
        query.prepare("SELECT COUNT(*) FROM applications");
    }
    
    if (query.exec() && query.next()) {
        return query.value(0).toInt();
    }
    return 0;
}

int Database::getPaymentCount(const QString& status)
{
    QSqlQuery query;
    if (!status.isEmpty()) {
        query.prepare("SELECT COUNT(*) FROM payments WHERE status = ?");
        query.bindValue(0, status);
    } else {
        query.prepare("SELECT COUNT(*) FROM payments");
    }
    
    if (query.exec() && query.next()) {
        return query.value(0).toInt();
    }
    return 0;
}