#include "MainWindow.h"
#include "ui_MainWindow.h"
#include "DashboardWidget.h"
#include "SoftwareCopyrightDialog.h"
#include "TrademarkDialog.h"
#include "PatentDialog.h"
#include "ProgressTrackerWidget.h"
#include "SettingsDialog.h"
#include "src/utils/Logger.h"
#include <QMenuBar>
#include <QToolBar>
#include <QStatusBar>
#include <QLabel>
#include <QMessageBox>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), ui(new Ui::MainWindow),
      m_stackedWidget(new QStackedWidget(this)),
      m_softwareCopyrightDialog(nullptr),
      m_trademarkDialog(nullptr),
      m_patentDialog(nullptr),
      m_settingsDialog(nullptr)
{
    ui->setupUi(this);
    
    setupUI();
    setupMenuBar();
    setupToolBar();
    setupStatusBar();
    loadStyleSheet();
    
    LOG_INFO("主窗口创建完成");
}

MainWindow::~MainWindow()
{
    delete ui;
    LOG_INFO("主窗口销毁");
}

void MainWindow::setupUI()
{
    setWindowTitle("知识产权申请管理系统 v1.0.0");
    resize(1200, 800);
    
    // 创建仪表板
    m_dashboardWidget = new DashboardWidget(this);
    m_stackedWidget->addWidget(m_dashboardWidget);
    
    // 创建进度追踪器
    m_progressTrackerWidget = new ProgressTrackerWidget(this);
    m_stackedWidget->addWidget(m_progressTrackerWidget);
    
    // 设置中央部件
    setCentralWidget(m_stackedWidget);
}

void MainWindow::setupMenuBar()
{
    QMenuBar* menuBar = new QMenuBar(this);
    
    // 文件菜单
    QMenu* fileMenu = menuBar->addMenu("文件(&F)");
    fileMenu->addAction("新建软著申请", this, &MainWindow::showSoftwareCopyrightDialog, QKeySequence::New);
    fileMenu->addAction("新建商标申请", this, &MainWindow::showTrademarkDialog, QKeySequence("Ctrl+T"));
    fileMenu->addAction("新建专利申请", this, &MainWindow::showPatentDialog, QKeySequence("Ctrl+P"));
    fileMenu->addSeparator();
    fileMenu->addAction("进度跟踪", this, &MainWindow::showProgressTracker, QKeySequence("Ctrl+K"));
    fileMenu->addSeparator();
    fileMenu->addAction("设置", this, &MainWindow::showSettings, QKeySequence("Ctrl+,"));
    fileMenu->addAction("退出", this, &MainWindow::on_actionExit_triggered, QKeySequence::Quit);
    
    // 帮助菜单
    QMenu* helpMenu = menuBar->addMenu("帮助(&H)");
    helpMenu->addAction("关于", this, &MainWindow::on_actionAbout_triggered);
    
    setMenuBar(menuBar);
}

void MainWindow::setupToolBar()
{
    QToolBar* toolBar = new QToolBar("主工具栏");
    toolBar->setToolButtonStyle(Qt::ToolButtonTextUnderIcon);
    
    toolBar->addAction("📊 仪表板", this, &MainWindow::switchToDashboard);
    toolBar->addSeparator();
    toolBar->addAction("📝 软著申请", this, &MainWindow::showSoftwareCopyrightDialog);
    toolBar->addAction("®️ 商标申请", this, &MainWindow::showTrademarkDialog);
    toolBar->addAction("💡 专利申请", this, &MainWindow::showPatentDialog);
    toolBar->addSeparator();
    toolBar->addAction("📈 进度跟踪", this, &MainWindow::showProgressTracker);
    
    addToolBar(toolBar);
}

void MainWindow::setupStatusBar()
{
    QStatusBar* statusBar = new QStatusBar(this);
    
    QLabel* statusLabel = new QLabel("就绪");
    statusBar->addWidget(statusLabel);
    
    setStatusBar(statusBar);
}

void MainWindow::loadStyleSheet()
{
    // TODO: 从资源文件加载 QSS 样式表
    // QFile styleFile(":/styles/style.qss");
    // if (styleFile.open(QFile::ReadOnly)) {
    //     QString styleSheet = QLatin1String(styleFile.readAll());
    //     setStyleSheet(styleSheet);
    // }
}

void MainWindow::switchToDashboard()
{
    m_stackedWidget->setCurrentWidget(m_dashboardWidget);
    setWindowTitle("知识产权申请管理系统 - 仪表板");
}

void MainWindow::showSoftwareCopyrightDialog()
{
    if (!m_softwareCopyrightDialog) {
        m_softwareCopyrightDialog = new SoftwareCopyrightDialog(this);
    }
    m_softwareCopyrightDialog->exec();
}

void MainWindow::showTrademarkDialog()
{
    if (!m_trademarkDialog) {
        m_trademarkDialog = new TrademarkDialog(this);
    }
    m_trademarkDialog->exec();
}

void MainWindow::showPatentDialog()
{
    if (!m_patentDialog) {
        m_patentDialog = new PatentDialog(this);
    }
    m_patentDialog->exec();
}

void MainWindow::showProgressTracker()
{
    m_stackedWidget->setCurrentWidget(m_progressTrackerWidget);
    setWindowTitle("知识产权申请管理系统 - 进度跟踪");
}

void MainWindow::showSettings()
{
    if (!m_settingsDialog) {
        m_settingsDialog = new SettingsDialog(this);
    }
    m_settingsDialog->exec();
}

void MainWindow::on_actionSoftwareCopyright_triggered() { showSoftwareCopyrightDialog(); }
void MainWindow::on_actionTrademark_triggered() { showTrademarkDialog(); }
void MainWindow::on_actionPatent_triggered() { showPatentDialog(); }
void MainWindow::on_actionProgressTracker_triggered() { showProgressTracker(); }
void MainWindow::on_actionSettings_triggered() { showSettings(); }
void MainWindow::on_actionAbout_triggered()
{
    QMessageBox::about(this, "关于",
        "知识产权申请管理系统 v1.0.0\n\n"
        "集成软件著作权、商标、专利申请管理\n"
        "AI 自动生成申请文件\n"
        "在线付费与进度跟踪\n\n"
        "© 2024 TradeMind");
}
void MainWindow::on_actionExit_triggered() { close(); }