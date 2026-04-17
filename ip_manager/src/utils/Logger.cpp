#include "Logger.h"

QFile* Logger::m_logFile = nullptr;
QTextStream* Logger::m_logStream = nullptr;
QMutex Logger::m_mutex;
LogLevel Logger::m_currentLevel = LogLevel::DEBUG;
bool Logger::m_initialized = false;

void Logger::init(const QString& logPath)
{
    QMutexLocker locker(&m_mutex);
    
    if (m_initialized) {
        return;
    }
    
    // 获取日志路径
    QString path = logPath;
    if (path.isEmpty()) {
        path = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) 
               + "/logs";
    }
    
    // 创建日志目录
    QDir().mkpath(path);
    
    // 创建日志文件
    QString logFileName = path + "/ip_manager_" 
                         + QDateTime::currentDateTime().toString("yyyyMMdd") 
                         + ".log";
    
    m_logFile = new QFile(logFileName);
    if (m_logFile->open(QIODevice::WriteOnly | QIODevice::Append | QIODevice::Text)) {
        m_logStream = new QTextStream(m_logFile);
        m_initialized = true;
        
        info("日志系统初始化完成: " + logFileName);
    } else {
        std::cerr << "Failed to create log file: " << logFileName.toStdString() << std::endl;
        delete m_logFile;
        m_logFile = nullptr;
    }
}

void Logger::shutdown()
{
    QMutexLocker locker(&m_mutex);
    
    if (m_logStream) {
        info("日志系统关闭");
        delete m_logStream;
        m_logStream = nullptr;
    }
    
    if (m_logFile) {
        m_logFile->close();
        delete m_logFile;
        m_logFile = nullptr;
    }
    
    m_initialized = false;
}

void Logger::log(LogLevel level, const QString& message)
{
    if (level < m_currentLevel) {
        return;
    }
    
    QMutexLocker locker(&m_mutex);
    
    QString logEntry = QString("[%1] [%2] %3")
        .arg(getCurrentTime())
        .arg(levelToString(level))
        .arg(message);
    
    // 输出到文件
    if (m_logStream) {
        *m_logStream << logEntry << "\n";
        m_logStream->flush();
    }
    
    // 输出到控制台
    switch (level) {
        case LogLevel::DEBUG:
            qDebug().noquote() << logEntry;
            break;
        case LogLevel::INFO:
            qDebug().noquote() << logEntry;
            break;
        case LogLevel::WARNING:
            qWarning().noquote() << logEntry;
            break;
        case LogLevel::ERROR:
            qCritical().noquote() << logEntry;
            break;
        case LogLevel::CRITICAL:
            qCritical().noquote() << logEntry;
            break;
    }
}

void Logger::debug(const QString& message) { log(LogLevel::DEBUG, message); }
void Logger::info(const QString& message) { log(LogLevel::INFO, message); }
void Logger::warning(const QString& message) { log(LogLevel::WARNING, message); }
void Logger::error(const QString& message) { log(LogLevel::ERROR, message); }
void Logger::critical(const QString& message) { log(LogLevel::CRITICAL, message); }

void Logger::setLogLevel(LogLevel level)
{
    QMutexLocker locker(&m_mutex);
    m_currentLevel = level;
}

LogLevel Logger::getLogLevel()
{
    QMutexLocker locker(&m_mutex);
    return m_currentLevel;
}

QString Logger::levelToString(LogLevel level)
{
    switch (level) {
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO: return "INFO";
        case LogLevel::WARNING: return "WARNING";
        case LogLevel::ERROR: return "ERROR";
        case LogLevel::CRITICAL: return "CRITICAL";
        default: return "UNKNOWN";
    }
}

QString Logger::getCurrentTime()
{
    return QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss.zzz");
}