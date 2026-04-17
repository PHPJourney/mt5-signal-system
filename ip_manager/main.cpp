// main.cpp - 程序入口
#include "ui/MainWindow.h"
#include "src/core/Database.h"
#include "src/core/ConfigManager.h"
#include "src/utils/Logger.h"
#include <QApplication>
#include <QStyleFactory>
#include <QFont>
#include <QTranslator>
#include <QLocale>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    
    // 设置应用信息
    app.setApplicationName("知识产权申请管理系统");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("TradeMind");
    app.setOrganizationDomain("trademind.cn");
    
    // 初始化日志系统
    Logger::init();
    LOG_INFO("应用程序启动");
    
    // 初始化数据库
    if (!Database::init()) {
        LOG_ERROR("数据库初始化失败");
        return -1;
    }
    
    // 初始化配置管理器
    ConfigManager::instance().load();
    
    // 设置全局样式
    QApplication::setStyle(QStyleFactory::create("Fusion"));
    
    // 加载翻译（可选）
    QTranslator translator;
    QString locale = QLocale::system().name();
    if (translator.load(QString(":/translations/ip_manager_%1.qm").arg(locale))) {
        app.installTranslator(&translator);
    }
    
    // 创建并显示主窗口
    MainWindow mainWindow;
    mainWindow.show();
    
    LOG_INFO("主窗口显示");
    
    int result = app.exec();
    
    // 清理资源
    Database::close();
    Logger::shutdown();
    
    return result;
}