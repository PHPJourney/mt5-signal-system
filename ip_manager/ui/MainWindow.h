#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QStackedWidget>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class DashboardWidget;
class SoftwareCopyrightDialog;
class TrademarkDialog;
class PatentDialog;
class ProgressTrackerWidget;
class SettingsDialog;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    // 菜单动作
    void on_actionSoftwareCopyright_triggered();
    void on_actionTrademark_triggered();
    void on_actionPatent_triggered();
    void on_actionProgressTracker_triggered();
    void on_actionSettings_triggered();
    void on_actionAbout_triggered();
    void on_actionExit_triggered();
    
    // 导航切换
    void switchToDashboard();
    void showSoftwareCopyrightDialog();
    void showTrademarkDialog();
    void showPatentDialog();
    void showProgressTracker();
    void showSettings();

private:
    void setupUI();
    void setupMenuBar();
    void setupToolBar();
    void setupStatusBar();
    void loadStyleSheet();
    
    Ui::MainWindow *ui;
    QStackedWidget* m_stackedWidget;
    DashboardWidget* m_dashboardWidget;
    SoftwareCopyrightDialog* m_softwareCopyrightDialog;
    TrademarkDialog* m_trademarkDialog;
    PatentDialog* m_patentDialog;
    ProgressTrackerWidget* m_progressTrackerWidget;
    SettingsDialog* m_settingsDialog;
};

#endif // MAINWINDOW_H