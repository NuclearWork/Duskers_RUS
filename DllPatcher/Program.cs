using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Mono.Cecil;
using Mono.Cecil.Cil;

namespace DllPatcher
{
    class Program
    {
        static void Main(string[] args)
        {
            // Поддержка аргументов командной строки для гибкой сборки
            string dbPath = args.Length > 0 ? args[0] : Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "Translation", "ru_database.json"));
            string originalDll = args.Length > 1 ? args[1] : @"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data\Managed\Assembly-CSharp.dll";
            string patchedDll = args.Length > 2 ? args[2] : Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "Patched_RU", "Assembly-CSharp.dll"));

            // Проверка наличия базы переводов
            if (!File.Exists(dbPath))
            {
                // Попробуем относительный путь от текущей папки
                if (File.Exists("Translation/ru_database.json"))
                    dbPath = Path.GetFullPath("Translation/ru_database.json");
                else if (File.Exists("../Translation/ru_database.json"))
                    dbPath = Path.GetFullPath("../Translation/ru_database.json");
                else
                {
                    Console.WriteLine($"[!] Ошибка: База переводов не найдена по пути: {dbPath}");
                    return;
                }
            }

            if (!File.Exists(originalDll))
            {
                Console.WriteLine($"[!] Ошибка: Исходная DLL не найдена: {originalDll}");
                return;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(patchedDll)!);

            // Читаем базу переводов
            string jsonString = File.ReadAllText(dbPath);
            var translations = JsonSerializer.Deserialize<Dictionary<string, string>>(jsonString);

            if (translations == null)
            {
                Console.WriteLine("[!] Ошибка: База переводов пуста или некорректна.");
                return;
            }

            // Фильтруем только DLL строки
            var dllTranslations = new Dictionary<string, string>();
            foreach (var kvp in translations)
            {
                if (kvp.Key.StartsWith("dll::") && !string.IsNullOrWhiteSpace(kvp.Value))
                {
                    dllTranslations[kvp.Key] = kvp.Value;
                }
            }

            Console.WriteLine($"Найдено {dllTranslations.Count} строк для инъекции в DLL...");

            // Грузим DLL
            using var module = ModuleDefinition.ReadModule(originalDll, new ReaderParameters { ReadWrite = false });

            int injectedCount = 0;

            foreach (var type in module.Types)
            {
                foreach (var method in type.Methods)
                {
                    if (!method.HasBody) continue;

                    foreach (var instruction in method.Body.Instructions)
                    {
                        if (instruction.OpCode == OpCodes.Ldstr)
                        {
                            string offsetHex = instruction.Offset.ToString("X4");
                            string key = $"dll::{type.FullName}::{method.Name}::{offsetHex}";

                            if (dllTranslations.TryGetValue(key, out string? ruText))
                            {
                                string? orig = instruction.Operand as string;
                                if (ruText != orig)
                                {
                                    instruction.Operand = ruText;
                                    injectedCount++;
                                }
                            }
                        }
                    }
                }
            }

            // Сохраняем патченную DLL
            module.Write(patchedDll);
            Console.WriteLine($"Успешно пропатчено {injectedCount} строк. Сохранено в: {patchedDll}");
        }
    }
}
