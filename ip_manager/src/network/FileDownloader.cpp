#include "FileDownloader.h"
#include "src/utils/Logger.h"
#include <QDir>
#include <QFileInfo>

FileDownloader::FileDownloader(QObject *parent)
    : QObject(parent), m_networkManager(new QNetworkAccessManager(this)),
      m_file(nullptr), m_progress(0)
{
    LOG_INFO("文件下载器初始化完成");
}

void FileDownloader::downloadCertificate(const QString& url, const QString& outputPath)
{
    downloadFile(url, outputPath);
}

void FileDownloader::downloadFile(const QString& url, const QString& outputPath)
{
    LOG_INFO("开始下载文件: " + url);
    
    // 创建输出目录
    QFileInfo fileInfo(outputPath);
    QDir().mkpath(fileInfo.absolutePath());
    
    m_file = new QFile(outputPath);
    if (!m_file->open(QIODevice::WriteOnly)) {
        QString error = "无法创建文件: " + outputPath;
        LOG_ERROR(error);
        emit downloadError(error);
        delete m_file;
        m_file = nullptr;
        return;
    }
    
    QNetworkRequest request(QUrl(url));
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute, true);
    
    QNetworkReply* reply = m_networkManager->get(request);
    
    connect(reply, &QNetworkReply::downloadProgress, this, &FileDownloader::onDownloadProgress);
    connect(reply, &QNetworkReply::finished, this, &FileDownloader::onDownloadFinished);
    connect(reply, QOverload<QNetworkReply::NetworkError>::of(&QNetworkReply::error),
            this, &FileDownloader::onDownloadError);
    
    m_progress = 0;
    emit downloadProgress(0);
}

void FileDownloader::onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal)
{
    if (bytesTotal > 0) {
        m_progress = static_cast<int>((bytesReceived * 100) / bytesTotal);
        emit downloadProgress(m_progress);
    }
}

void FileDownloader::onDownloadFinished()
{
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    
    if (reply->error() == QNetworkReply::NoError) {
        if (m_file) {
            m_file->write(reply->readAll());
            m_file->close();
            
            QString filePath = m_file->fileName();
            LOG_INFO("文件下载完成: " + filePath);
            emit downloadCompleted(filePath);
            
            delete m_file;
            m_file = nullptr;
        }
    } else {
        onDownloadError(reply->error());
    }
    
    reply->deleteLater();
}

void FileDownloader::onDownloadError(QNetworkReply::NetworkError error)
{
    QString errorStr = "下载失败: " + QString::number(error);
    LOG_ERROR(errorStr);
    emit downloadError(errorStr);
    
    if (m_file) {
        m_file->remove();
        delete m_file;
        m_file = nullptr;
    }
}