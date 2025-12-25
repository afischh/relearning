import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const QuietLogosApp());
}

class QuietLogosApp extends StatelessWidget {
  const QuietLogosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'quiet_logos — writer',
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
      ),
      home: const WriterScreen(),
    );
  }
}

class WriterScreen extends StatefulWidget {
  const WriterScreen({super.key});

  @override
  State<WriterScreen> createState() => _WriterScreenState();
}

class _WriterScreenState extends State<WriterScreen> {
  final _date = TextEditingController();
  final _title = TextEditingController();
  final _quiet = TextEditingController();
  final _tech = TextEditingController();

  bool _busy = false;
  String _status =
      'Готов к записи. Сервер должен работать на 127.0.0.1:8008';

  final Uri _submitUrl = Uri.parse('http://127.0.0.1:8008/submit');

  @override
  void dispose() {
    _date.dispose();
    _title.dispose();
    _quiet.dispose();
    _tech.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _status = 'Отправляю…';
    });

    try {
      final form = <String, String>{
        'd': _date.text.trim(),
        'title': _title.text.trim(),
        'quiet': _quiet.text,
        'tech': _tech.text,
      };

      final resp = await http.post(
        _submitUrl,
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: form.entries
            .map((e) =>
                '${Uri.encodeQueryComponent(e.key)}=${Uri.encodeQueryComponent(e.value)}')
            .join('&'),
      );

      if (resp.statusCode == 200) {
        setState(() {
          _status = 'Готово. Запись сохранена и сайт пересобран.';
        });
      } else {
        setState(() {
          _status =
              'Ошибка сервера: ${resp.statusCode}\n${_safeSnippet(resp.body)}';
        });
      }
    } catch (e) {
      setState(() {
        _status =
            'Ошибка запроса: $e\nПроверь, что journal_server.py запущен.';
      });
    } finally {
      setState(() {
        _busy = false;
      });
    }
  }

  void _openIndex() async {
    const path =
        'file:///home/alex/relearning/docs/log/index.html';
    try {
      await Process.run('xdg-open', [path]);
      setState(() {
        _status = 'Лента открыта в браузере.';
      });
    } catch (e) {
      setState(() {
        _status = 'Не удалось открыть ленту: $e';
      });
    }
  }

  String _safeSnippet(String s) {
    final t = s.replaceAll(RegExp(r'\s+'), ' ').trim();
    return t.length > 400 ? '${t.substring(0, 400)}…' : t;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('quiet_logos — новая запись'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 980),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: ListView(
              children: [
                _Card(
                  title: 'Метаданные',
                  child: Column(
                    children: [
                      TextField(
                        controller: _date,
                        decoration: const InputDecoration(
                          labelText: 'Дата (YYYY-MM-DD)',
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _title,
                        decoration: const InputDecoration(
                          labelText: 'Заголовок',
                        ),
                      ),
                    ],
                  ),
                ),
                _Card(
                  title: 'quiet',
                  child: TextField(
                    controller: _quiet,
                    minLines: 6,
                    maxLines: 14,
                  ),
                ),
                _Card(
                  title: 'tech',
                  child: TextField(
                    controller: _tech,
                    minLines: 6,
                    maxLines: 14,
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: _busy ? null : _submit,
                  child: Text(
                      _busy ? 'Отправляю…' : 'Сохранить → пересобрать сайт'),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  onPressed: _openIndex,
                  child: const Text('Открыть ленту'),
                ),
                const SizedBox(height: 12),
                Text(
                  _status,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.75),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}
