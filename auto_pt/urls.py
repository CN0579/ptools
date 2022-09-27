from django.urls import path

from auto_pt import views

urlpatterns = [
    path(r'get_tasks', views.get_tasks, name='get_tasks'),
    path(r'add_task', views.get_tasks, name='add_task'),
    path(r'exec_task', views.exec_task, name='exec_task'),
    path(r'test_field', views.test_field, name='test_field'),
    path(r'test_notify', views.test_notify, name='test_notify'),
    path(r'update', views.update_page, name='update_page'),
    path(r'do_restart', views.do_restart, name='do_restart'),
    path(r'do_update', views.do_update, name='do_update'),
    path(r'import_from_ptpp', views.import_from_ptpp, name='import_from_ptpp'),
    path(r'page_downloading', views.page_downloading, name='page_downloading'),
    path(r'get_downloader', views.get_downloader, name='get_downloader'),
    path(r'downloading', views.get_downloading, name='downloading'),
    path(r'torrent_info_page', views.render_torrents_page, name='torrent_info_page'),
    path(r'get_torrent_info_list', views.get_torrent_info_list, name='get_torrent_info_list'),
    path(r'do_sql', views.do_sql, name='do_sql'),
]
