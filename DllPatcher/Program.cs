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
            string dbPath = @"C:\Users\user\Documents\GITHUB\Duskers_RUS\Translation\ru_database.json";
            string originalDll = @"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data\Managed\Assembly-CSharp.dll";
            string patchedDll = @"C:\Users\user\Documents\GITHUB\Duskers_RUS\Patched_RU\Assembly-CSharp.dll";

            if (!File.Exists(dbPath))
            {
                Console.WriteLine("База переводов не найдена.");
                return;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(patchedDll));

            // Читаем базу переводов
            string jsonString = File.ReadAllText(dbPath);
            var translations = JsonSerializer.Deserialize<Dictionary<string, string>>(jsonString);

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

                            if (dllTranslations.TryGetValue(key, out string ruText))
                            {
                                // Важная проверка: не инжектим, если перевод совпадает с оригиналом
                                string orig = instruction.Operand as string;
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
            Console.WriteLine($"Успешно пропатчено {injectedCount} строк. Сохранено в {patchedDll}");
        }
    }
}
