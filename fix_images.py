#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления размеров изображений в датасете

Этот скрипт проверяет и исправляет изображения с некорректными размерами.
Проблема: изображения имеют нечетные размеры (158×158, 128×129 и т.д.)
Решение: приведение всех изображений к одному размеру

Автор: ML-NIKITA-NPD
"""

import os
import sys
import argparse
from PIL import Image
import numpy as np
from tqdm import tqdm
import shutil
from datetime import datetime


def check_image_sizes(dataset_path):
    """
    Проверка размеров всех изображений в датасете.

    Параметры:
    - dataset_path: путь к корневой папке датасета

    Возвращает:
    - size_stats: словарь со статистикой по размерам
    - problematic_images: список изображений с проблемными размерами
    """
    print("🔍 Анализ размеров изображений...\n")

    size_stats = {}
    problematic_images = []
    all_images = []

    # Проход по всем классам
    class_folders = [f for f in os.listdir(dataset_path)
                     if os.path.isdir(os.path.join(dataset_path, f))]

    for class_name in class_folders:
        class_path = os.path.join(dataset_path, class_name)
        image_files = [f for f in os.listdir(class_path)
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        for img_file in image_files:
            img_path = os.path.join(class_path, img_file)

            try:
                img = Image.open(img_path)
                size = img.size  # (width, height)

                # Статистика
                size_key = f"{size[0]}×{size[1]}"
                size_stats[size_key] = size_stats.get(size_key, 0) + 1

                # Проверка на нечетные размеры или несоответствие
                if size[0] != size[1] or size[0] % 2 != 0 or size[1] % 2 != 0:
                    problematic_images.append({
                        'path': img_path,
                        'class': class_name,
                        'filename': img_file,
                        'size': size
                    })

                all_images.append({
                    'path': img_path,
                    'class': class_name,
                    'filename': img_file,
                    'size': size
                })

            except Exception as e:
                print(f"⚠ Ошибка чтения {img_path}: {e}")

    # Вывод статистики
    print("📊 СТАТИСТИКА РАЗМЕРОВ:")
    print("="*50)
    for size, count in sorted(size_stats.items()):
        percentage = count / len(all_images) * 100
        print(f"  {size}: {count} изображений ({percentage:.1f}%)")
    print("="*50)

    print(f"\nВсего изображений: {len(all_images)}")
    print(f"Проблемных изображений: {len(problematic_images)}")

    return size_stats, problematic_images, all_images


def fix_images(images_list, target_size, output_path=None, create_backup=False):
    """
    Исправление размеров изображений.

    Параметры:
    - images_list: список словарей с информацией об изображениях
    - target_size: целевой размер (ширина, высота)
    - output_path: путь для сохранения (если None - перезапись оригиналов)
    - create_backup: создавать резервную копию перед изменением

    Возвращает:
    - fixed_count: количество исправленных изображений
    """
    print(f"\n🔧 Исправление изображений до размера {target_size[0]}×{target_size[1]}...\n")

    if create_backup and not output_path:
        # Создание резервной копии
        backup_path = images_list[0]['path'].rsplit('/', 2)[0] + '_backup'
        print(f"📦 Создание резервной копии в {backup_path}...")

        # Копирование всей структуры
        original_path = images_list[0]['path'].rsplit('/', 2)[0]
        if not os.path.exists(backup_path):
            shutil.copytree(original_path, backup_path)
            print("✓ Резервная копия создана\n")

    fixed_count = 0
    errors = []

    for img_info in tqdm(images_list, desc="Обработка"):
        img_path = img_info['path']

        # Определение выходного пути
        if output_path:
            # Создание аналогичной структуры в output_path
            rel_path = os.path.relpath(img_path, images_list[0]['path'].rsplit('/', 2)[0])
            out_path = os.path.join(output_path, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        else:
            out_path = img_path

        try:
            # Открытие изображения
            img = Image.open(img_path)
            original_size = img.size

            # Изменение размера только если нужно
            if original_size != target_size:
                # Метод LANCZOS для качественного ресайза
                img_resized = img.resize(target_size, Image.Resampling.LANCZOS)

                # Сохранение
                img_resized.save(out_path, quality=95, optimize=True)
                fixed_count += 1
            elif output_path:
                # Копирование без изменений
                img.save(out_path, quality=95, optimize=True)

        except Exception as e:
            errors.append(f"{img_path}: {e}")

    # Вывод результатов
    print(f"\n✓ Обработка завершена!")
    print(f"  Исправлено изображений: {fixed_count}")

    if errors:
        print(f"\n⚠ Ошибки ({len(errors)}):")
        for error in errors[:10]:  # Показать первые 10 ошибок
            print(f"  {error}")
        if len(errors) > 10:
            print(f"  ... и еще {len(errors) - 10} ошибок")

    return fixed_count


def generate_report(size_stats, problematic_images, output_file='image_analysis_report.txt'):
    """
    Генерация текстового отчета об анализе изображений.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("ОТЧЕТ ОБ АНАЛИЗЕ ИЗОБРАЖЕНИЙ\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")

        f.write("СТАТИСТИКА РАЗМЕРОВ:\n")
        f.write("-"*60 + "\n")
        for size, count in sorted(size_stats.items()):
            f.write(f"  {size}: {count} изображений\n")

        f.write(f"\nВсего проблемных изображений: {len(problematic_images)}\n\n")

        if problematic_images:
            f.write("СПИСОК ПРОБЛЕМНЫХ ИЗОБРАЖЕНИЙ:\n")
            f.write("-"*60 + "\n")

            # Группировка по классам
            by_class = {}
            for img in problematic_images:
                class_name = img['class']
                if class_name not in by_class:
                    by_class[class_name] = []
                by_class[class_name].append(img)

            for class_name, images in sorted(by_class.items()):
                f.write(f"\nКласс: {class_name} ({len(images)} изображений)\n")
                for img in images[:5]:  # Первые 5 из каждого класса
                    f.write(f"  - {img['filename']}: {img['size'][0]}×{img['size'][1]}\n")
                if len(images) > 5:
                    f.write(f"  ... и еще {len(images) - 5} изображений\n")

    print(f"\n✓ Отчет сохранен в {output_file}")


def main():
    """
    Главная функция скрипта.
    """
    parser = argparse.ArgumentParser(
        description='Исправление размеров изображений в датасете',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  1. Анализ без изменений:
     python fix_images.py /path/to/dataset --analyze-only

  2. Исправление с резервной копией:
     python fix_images.py /path/to/dataset --fix --backup

  3. Исправление с сохранением в новую папку:
     python fix_images.py /path/to/dataset --fix --output /path/to/fixed_dataset

  4. Исправление только проблемных изображений:
     python fix_images.py /path/to/dataset --fix --problematic-only
        """
    )

    parser.add_argument('dataset_path', type=str,
                       help='Путь к папке с датасетом')
    parser.add_argument('--target-size', type=int, nargs=2, default=[128, 128],
                       metavar=('WIDTH', 'HEIGHT'),
                       help='Целевой размер изображений (по умолчанию: 128 128)')
    parser.add_argument('--fix', action='store_true',
                       help='Исправить изображения (без этого флага только анализ)')
    parser.add_argument('--output', type=str, default=None,
                       help='Путь для сохранения исправленных изображений (опционально)')
    parser.add_argument('--backup', action='store_true',
                       help='Создать резервную копию перед изменением оригиналов')
    parser.add_argument('--problematic-only', action='store_true',
                       help='Исправлять только проблемные изображения')
    parser.add_argument('--report', type=str, default='image_analysis_report.txt',
                       help='Имя файла отчета (по умолчанию: image_analysis_report.txt)')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Только анализ без исправлений (синоним для отсутствия --fix)')

    args = parser.parse_args()

    # Проверка существования датасета
    if not os.path.exists(args.dataset_path):
        print(f"❌ Ошибка: Путь {args.dataset_path} не существует!")
        sys.exit(1)

    print("="*60)
    print("СКРИПТ ИСПРАВЛЕНИЯ ИЗОБРАЖЕНИЙ")
    print("="*60)
    print(f"Датасет: {args.dataset_path}")
    print(f"Целевой размер: {args.target_size[0]}×{args.target_size[1]}")
    print("="*60 + "\n")

    # Анализ изображений
    size_stats, problematic_images, all_images = check_image_sizes(args.dataset_path)

    # Генерация отчета
    generate_report(size_stats, problematic_images, args.report)

    # Исправление изображений
    if args.fix and not args.analyze_only:
        # Определение списка изображений для исправления
        if args.problematic_only:
            images_to_fix = problematic_images
            print(f"\n📝 Будут исправлены только проблемные изображения ({len(images_to_fix)})")
        else:
            images_to_fix = all_images
            print(f"\n📝 Будут обработаны все изображения ({len(images_to_fix)})")

        # Подтверждение
        if not args.output and not args.backup:
            print("\n⚠ ВНИМАНИЕ: Оригинальные изображения будут перезаписаны!")
            response = input("Продолжить? (yes/no): ")
            if response.lower() != 'yes':
                print("Операция отменена.")
                sys.exit(0)

        # Исправление
        target_size = tuple(args.target_size)
        fixed_count = fix_images(
            images_to_fix,
            target_size,
            args.output,
            args.backup
        )

        print("\n" + "="*60)
        print("✓ РАБОТА ЗАВЕРШЕНА")
        print("="*60)
        print(f"Исправлено изображений: {fixed_count}")
        if args.output:
            print(f"Результат сохранен в: {args.output}")
        elif args.backup:
            backup_path = args.dataset_path + '_backup'
            print(f"Резервная копия: {backup_path}")
        print("="*60)
    else:
        print("\n💡 Для исправления изображений запустите скрипт с флагом --fix")
        print("   Пример: python fix_images.py /path/to/dataset --fix --backup")


if __name__ == '__main__':
    main()
