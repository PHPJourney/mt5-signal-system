#ifndef LOGGER_H
#define LOGGER_H

#include <QString>
#include <QDateTime>
#include <QFile>
#include <QTextStream>
#include <QMutex>
#include <QDir>
#include <QStandardPaths>
#include <QDebug>
#include <iostream>

enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL
};

class Logger
{
public:
    static void init(const QString& logPath = QString());
    static void shutdown();
    
    static void log(LogLevel level, const QString& message);
    static void debug(const QString& message);
    static void info(const QString& message);
    static void warning(const QString& message);
    static void error(const QString& message);
    static void critical(const QString& message);
    
    static void setLogLevel(LogLevel level);
    static LogLevel getLogLevel();
    
private:
    static QString levelToString(LogLevel level);
    static QString getCurrentTime();
    
    static QFile* m_logFile;
    static QTextStream* m_logStream;
    static QMutex m_mutex;
    static LogLevel m_currentLevel;
    static bool m_initialized;
};

// 便捷宏
#define LOG_DEBUG(msg) Logger::debug(msg)
#define LOG_INFO(msg) Logger::info(msg)
#define LOG_WARNING(msg) Logger::warning(msg)
#define LOG_ERROR(msg) Logger::error(msg)
#define LOG_CRITICAL(msg) Logger::critical(msg)

#endif // LOGGER_H