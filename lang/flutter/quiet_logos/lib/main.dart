import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

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
  String _status = 'Готов к записи. Режим: save → build → git push.';
  final List<String> _log = [];

  // Путь к корню репозитория — фиксирован явно
  final String _repoPath = '/home/alex/relearning';

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _date.text = _fmtDate(now);
  }

  @override
  void dispose() {
    _date.dispose();
    _title.dispose();
    _quiet.dispose();
    _tech.dispose();
    super.dispose();
  }

  String _fmtDate(DateTime d) {
    final y = d.year.toString().padLeft(4, '0');
    final m = d.month.toString().padLeft(2, '0');
    final day = d.day.toString().padLeft(2, '0');
    return '$y-$m-$day';
  }

  bool _validDate(String s) => RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(s);

  void _appendLog(String line) {
    setState(() {
      _log.add(line);
      if (_log.length > 1500) {
        _log.removeRange(0, _log.length - 1500);
      }
    });
  }

  String _buildMarkdown(String dateStr) {
    final title = _title.text.trim().isEmpty ? 'Запись' : _title.text.trim();
    final quiet = _quiet.text.trim();
    final tech = _tech.text.trim();

    return [
      '# $title',
      '',
      '- DATE: $dateStr',
      '',
      '## Quiet',
      quiet.isEmpty ? '_(пусто)_' : quiet,
      '',
      '## Tech',
      tech.isEmpty ? '_(пусто)_' : tech,
      '',
    ].join('\n');
  }

  Future<void> _saveMarkdown() async {
    final dateStr = _date.text.trim();
    if (!_validDate(dateStr)) {
      throw Exception('Некорректная дата. Ожидается формат YYYY-MM-DD.');
    }

    final mdPath = '$_repoPath/docs/log/$dateStr.md';
    final mdFile = File(mdPath);
    await mdFile.parent.create(recursive: true);

    final content = _buildMarkdown(dateStr);
    await mdFile.writeAsString(content, encoding: utf8);

    _appendLog('Saved: $mdPath');
  }

  Future<void> _saveBuildPush() async {
    if (_busy) return;

    setState(() {
      _busy = true;
      _status = 'Сохраняю и публикую…';
    });

    _appendLog('---');
    _appendLog('Save → Build → Push started');

    try {
      await _saveMarkdown();

      final dateStr = _date.text.trim();
      final scriptPath = 'tools/publish/git_publish.sh';

      final proc = await Process.start(
        'bash',
        [scriptPath, dateStr, 'Publish log $dateStr (via Flutter)'],
        workingDirectory: _repoPath,
        runInShell: false,
      );

      proc.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((line) => _appendLog(line));

      proc.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((line) => _appendLog('ERR: $line'));

      final exitCode = await proc.exitCode;

      setState(() {
        _status = exitCode == 0
            ? 'Готово. Запись сохранена, сайт собран и отправлен на GitHub.'
            : 'Ошибка публикации (code $exitCode). См. лог.';
      });
    } catch (e) {
      setState(() {
        _status = 'Ошибка: $e';
      });
    } finally {
      setState(() {
        _busy = false;
      });
    }
  }

  void _openIndex() async {
    const path = 'file:///home/alex/relearning/docs/log/index.html';
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
                  onPressed: _busy ? null : _saveBuildPush,
                  child: Text(_busy ? 'Публикую…' : 'Сохранить → собрать → push'),
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
                const SizedBox(height: 12),
                _Card(
                  title: 'Лог',
                  child: SizedBox(
                    height: 220,
                    child: SingleChildScrollView(
                      child: Text(
                        _log.join('\n'),
                        style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                      ),
                    ),
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
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}
