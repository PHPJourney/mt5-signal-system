#ifndef FILEDOWNLOADER_H
#define FILEDOWNLOADER_H

#include <QObject>
#include <QString>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QFile>

class FileDownloader : public QObject
{
    Q_OBJECT

public:
    explicit FileDownloader(QObject *parent = nullptr);
    
    // 下载证书
    void downloadCertificate(const QString& url, const QString& outputPath);
    
    // 下载文件
    void downloadFile(const QString& url, const QString& outputPath);
    
    // 获取下载进度
    int getProgress() const { return m_progress; }

signals:
    void downloadCompleted(const QString& filePath);
    void downloadProgress(int percent);
    void downloadError(const QString& error);

private slots:
    void onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal);
    void onDownloadFinished();
    void onDownloadError(QNetworkReply::NetworkError error);

private:
    QNetworkAccessManager* m_networkManager;
    QFile* m_file;
    int m_progress;
};

#endif // FILEDOWNLOADER_H